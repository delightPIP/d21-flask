# db.py : 수강 후기를 SQLite(파일 하나짜리 DB)에 저장하고 꺼내는 파일이에요
import sqlite3                                # SQLite 를 다루는 도구 (파이썬에 기본으로 들어 있어요)
from datetime import datetime, timedelta, timezone   # 날짜 · 시간을 다루는 도구
from pathlib import Path                      # 파일 경로를 편하게 다루는 도구

DB_PATH = Path(__file__).parent / "reviews.db"   # 이 파일 옆의 reviews.db (어느 폴더에서 서버를 켜도 같은 위치)
KST = timezone(timedelta(hours=9))            # 한국 시간 (배포 서버의 시계는 한국 시간이 아니에요)


def connect():                                # DB 에 연결하는 함수
    con = sqlite3.connect(DB_PATH)            # reviews.db 파일을 열어요 (없으면 새로 만들어요)
    con.row_factory = sqlite3.Row             # 꺼낸 줄을 r["nickname"] 처럼 칸 이름으로 읽을 수 있게 해요
    return con                                # 연결을 돌려줘요


def init_db():                                # 표를 만드는 함수 (앱이 시작될 때 한 번 실행해요)
    con = connect()                           # DB 에 연결하고
    with con:                                 # with 블록이 잘 끝나면 알아서 저장(commit)해 줘요
        con.execute("""
            CREATE TABLE IF NOT EXISTS reviews (                           -- 표가 없을 때만 만들어요
                id         INTEGER PRIMARY KEY AUTOINCREMENT,              -- 리뷰 번호 (자동으로 1, 2, 3…)
                class_id   INTEGER NOT NULL,                               -- 클래스 번호
                nickname   TEXT    NOT NULL,                               -- 닉네임
                rating     INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),-- 별점 (1~5 만)
                content    TEXT    NOT NULL,                               -- 내용
                created_at TEXT    NOT NULL                                -- 저장 시각
            )
        """)
    con.close()                               # 다 쓴 연결은 닫아요


def add_review(class_id, nickname, rating, content):   # 리뷰 하나를 넣는 함수
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")   # 지금 시각을 '2026-11-11 10:52:03' 모양 글자로
    con = connect()
    with con:                                 # 잘 끝나면 저장(commit), 에러가 나면 되돌려요
        con.execute(
            "INSERT INTO reviews (class_id, nickname, rating, content, created_at) "
            "VALUES (?, ?, ?, ?, ?)",         # SQL 은 틀만 적고, 사용자 값이 들어갈 곳은 ? 로 비워 둬요
            (class_id, nickname, rating, content, now),   # ? 자리에 순서대로 들어갈 값들 (값은 명령이 되지 않아요)
        )
    con.close()


def get_reviews(class_id):                    # 그 클래스의 리뷰를 최신순으로 꺼내는 함수
    con = connect()
    rows = con.execute(
        "SELECT id, nickname, rating, content, created_at FROM reviews "
        "WHERE class_id = ? ORDER BY id DESC",   # 그 클래스 것만, 번호가 큰(새로 넣은) 것부터
        (class_id,),                          # 값이 하나여도 쉼표가 있어야 해요
    ).fetchall()                              # 결과를 전부 가져와요
    con.close()
    return [dict(row) for row in rows]        # 한 줄씩 딕셔너리로 바꿔서 돌려줘요
