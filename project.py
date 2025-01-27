import csv
import inflect
from random import sample, choice
import re
import requests
import sqlite3
from sys import exit
from time import sleep
from typing import TypedDict

# calling engine for inflect library
p = inflect.engine()

# calling database and creating one if not existing
db_path: str = "users.db"
with sqlite3.connect(db_path) as db:
    cursor = db.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            username TEXT NOT NULL,
            total_score INTEGER NOT NULL DEFAULT 0,
            accuracy NUMERIC DEFAULT NULL,
            total_games INTEGER NOT NULL DEFAULT 0
        )
    """
    )


# class for dictionary type hinting
class WordDict(TypedDict):
    word: str
    meaning: str
    furigana: str
    romaji: str
    level: int


# * MAIN
def main():
    # *log the user
    strings: list[str] = [
        "1. I am already a user.",
        "2. I am new, I wish to create a new user.",
        "3. Exit the program",
    ]
    print(
        "Hello! And welcome to the Kanji and Kana Anki Quiz! Select one of the following options:"
    )
    a: int = loop_quest(*strings)

    match a:
        # validate user
        case 1:
            while True:
                user: str = input("Username: ").strip()
                if validate_user(user):
                    id_user: int = fetch_id(user)
                    break
                elif user == "1":
                    exit(1)
                else:
                    user: str = input(
                        "No user found. Retype the username or type 1 to exit the program."
                    ).strip()

        # create new user
        case 2:
            while True:
                print(
                    "Write your username. Only alphabetical and numerical characters allowed. Min 2 characters, max 10."
                )
                user: str = input("Username: ").strip()
                if validate_username(user):
                    # insert into db
                    with sqlite3.connect(db_path) as db:
                        cursor = db.cursor()
                        cursor.execute(
                            "INSERT INTO users (username) VALUES (?)", (user,)
                        )
                        db.commit()
                    id_user: int = fetch_id(user)
                    break
        case 3:
            exit()

    # *select what to do
    print(f"Welcome {user}! What do you wish to do?")
    strings2: list[str] = [
        "1. Play a game. Every game has 15 questions and you have 1 try to give the right answer.",
        "2. View my scores.",
        "3. Exit the program.",
    ]
    while True:
        action: int = loop_quest(*strings2)

        # view scores
        if action == 2:
            print(view_score(id_user, user))

        # exit
        if action == 3:
            exit()

        # *select game
        elif action == 1:
            print("What game do you want to play?")
            print("1. Write the kana in romaji.")
            print(
                "2. Write the corresponding kana of the kanji (you can select the level)."
            )
            print(
                "3. Write the corresponding kanji of the kana (you can select the level)."
            )
            while True:
                try:
                    choice: int = int(input("Write the corresponding number: ").strip())
                except ValueError:
                    print("Write a valid choice.")
                    continue
                if valid_choice(choice):
                    break

            # *play kana game
            if choice == 1:
                points: int
                percent: float
                points, percent = kana_game()
                # update scores in database
                update(id_user, points, percent)

            # *select level
            elif choice in [2, 3]:
                while True:
                    try:
                        level: int = int(
                            input(
                                "What JLPT level do you select? Write a number from 1 to 5: "
                            ).strip()
                        )
                    except ValueError:
                        print("Write a valid level.")
                        continue
                    if level > 5 or level < 1:
                        print("Write a valid level.")
                    else:
                        break

                # play kanji game
                points: int
                percent: float
                points, percent = kanji_game(choice, level)
                # update scores in database
                update(id_user, points, percent)

        # 1 sec timeout
        sleep(1)


def loop_quest(*strings: list[str]) -> int:
    # small function for looping
    while True:
        # string to print
        print(strings[0])
        print(strings[1])
        print(strings[2])
        # input
        try:
            a: int = int(input("Write the corresponding number: ").strip())
        # value error print
        except ValueError:
            print("Write a valid choice.")
            continue
        # loop break when bool True
        if valid_choice(a):
            return a


def validate_user(user: str) -> bool:
    # validate user in db case insensitive
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        # fetch for username
        result: tuple[str] = cursor.execute(
            "SELECT username FROM users WHERE LOWER(username) = LOWER(?)", (user,)
        ).fetchone()
        # if no user found return false
        if result is None:
            return False
    return True


def validate_username(user: str) -> bool:
    # check regex
    if re.search("^[a-zA-Z0-9]{2,10}$", user):
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            # check if user already exists
            result: tuple[str] = cursor.execute(
                "SELECT username FROM users WHERE LOWER(username) = LOWER(?)", (user,)
            ).fetchone()
            # if no user found then return true
            if result is None:
                return True
            else:
                print("Username already taken.")
                return False
    # return if regex None
    return False


def fetch_id(user: str) -> int:
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        # fetch user id
        user_id: tuple[int] = cursor.execute(
            "SELECT ID FROM users WHERE LOWER(username) = LOWER(?)", (user,)
        ).fetchone()
        id_user: int = user_id[0]
    return id_user


def view_score(id_user: int, user: str) -> str:
    score: str = ""
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        # fetch scores
        result: tuple[int, float, int] = cursor.execute(
            "SELECT total_score, accuracy, total_games FROM users WHERE ID = ?",
            (id_user,),
        ).fetchone()
        # result for new users
        if result == (0, None, 0):
            score = "No scores to view."
        # result for 1+ games
        else:
            score = f"{user} has {result[0]} total points with {round(result[1])}% correct answers in {result[2]} {p.plural("game", result[2])} total."
    return score


def valid_choice(action: int) -> bool:
    # check if int matches cases
    match action:
        case 1 | 2 | 3:
            return True
        case _:
            print("Write a valid choice")
            return False


def kana_game() -> tuple[int, float]:
    # create dict with kana csv
    kana: list[dict] = []

    with open("kana.csv") as file:
        reader = csv.DictReader(file)
        for row in reader:
            kana.append(
                {
                    "hiragana": row["hiragana"],
                    "katakana": row["katakana"],
                    "romaji": row["romaji"],
                }
            )

    # set points, loop and random ints list
    points: int = 0
    ex: int = 0
    randoms: list[int] = sample(range(len(kana) - 1), 15)

    # play game
    while ex < 15:
        kana_format: str = choice(["hiragana", "katakana"])
        print(f"{ex+1}. {kana[randoms[ex]][kana_format]}")
        answer: str = input("Answer: ").lower().strip()
        if answer == kana[randoms[ex]]["romaji"]:
            points += 1
            print("Correct!")
        else:
            print(f"Wrong! The right answer is {kana[randoms[ex]]['romaji']}.")

        ex += 1

    # accuracy
    accuracy: float = float(points) / 15 * 100

    print(f"You answered {points} questions correctly which correspond to {round(accuracy)}% of the total questions.")
    return points, accuracy


def check_kanji(word: str) -> bool:
    # check if fetched word has at least one kanji
    for c in word:
        if not ("\u3040" <= c <= "\u309F" or "\u30A0" <= c <= "\u30FF"):
            return True
    return False


def parse_kanji(word: str) -> str:
    # keeps only the kanji reading if the furigana output has additional readings
    out: list[str] = word.split("・")
    return out[0]


def kanji_game(choice: int, level: int) -> tuple[int, float]:
    print(
        "Please, write the WHOLE word in the answer, not only the reading of the kanji."
    )

    # set points and loop
    points: int = 0
    ex: int = 0

    # loop
    while ex < 15:

        # fetch word
        while True:
            try:
                response = requests.get(
                    f"https://jlpt-vocab-api.vercel.app/api/words/random?level={level}"
                )
                response.raise_for_status()
            except requests.HTTPError:
                print("Couldn't complete request!")
                exit(1)
            word: WordDict = response.json()
            if (word["word"] and word["furigana"] != "") and check_kanji(word["word"]):
                furigana: str = parse_kanji(word["furigana"])
                break

        # play game
        match choice:
            case 2:
                print(f"{ex+1}. {word['word']}")
            case 3:
                print(f"{ex+1}. furigana")
        answer: str = input("Answer: ").strip()
        if (choice == 2 and answer == furigana) or (
            choice == 3 and answer == word["word"]
        ):
            points += 1
            print("Correct!")

        else:
            correct = furigana if choice == 2 else word["word"]
            print(f"Wrong! The right answer is {correct}")
        ex += 1

    # accuracy
    accuracy: float = float(points) / 15 * 100

    print(f"You answered {points} questions correctly which correspond to {round(accuracy)}% of the total questions.")
    return points, accuracy


def update(id_user: int, points: int, accuracy: float) -> None:
    # fetch variables
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        # update games +1
        cursor.execute(
            "UPDATE users SET total_games = total_games + 1 WHERE id = ?", (id_user,)
        )
        acc: tuple[float] = cursor.execute(
            "SELECT accuracy FROM users WHERE id = ?", (id_user,)
        ).fetchone()

        new_acc: float = 0
        old_acc: float = acc[0]
        # calculate accuracy
        if old_acc is not None:
            new_acc = (old_acc + accuracy) / 2
        else:
            new_acc = accuracy

        # update database
        cursor.execute(
            "UPDATE users SET total_score = total_score + ?, accuracy = ? WHERE id = ?",
            (
                points,
                new_acc,
                id_user,
            ),
        )
        db.commit()
    return


if __name__ == "__main__":
    main()
