# 클래스로 마켓 (D21 · Flask ②)

동네 원데이 클래스를 구경하고, 수강 후기를 남기고, 마음에 드는 클래스를 찜하는 웹 서비스예요.

배포 주소: (Render 배포 뒤에 적기)

## 내 컴퓨터에서 켜기
```
pip install -r requirements.txt
flask --app app run --debug
```
처음 한 번은 `.env.example` 을 `.env` 로 복사하고 `SECRET_KEY` 를 채워요.

## 무료 배포의 한계
15분 쉬면 잠들어서 첫 접속이 1분쯤 걸려요. 서버가 다시 시작되면 `reviews.db` 가 지워져 남긴 후기가 사라질 수 있어요.
