<h1>로컬 데이터베이스 생성 및 연결 가이드라인</h1> 
MySQL 사용

<br/><hr/>
<h3>MySQL 테이블 생성</h3>

1. MySQL 접속
```bash
mysql -u root -p
```
2. 데이터베이스 생성 및 전환
```sql
CREATE DATABASE npcb_db;
USE npcb_db;
```
3. child 테이블 생성
```sql
CREATE TABLE npcb_db.child(
id INT PRIMARY KEY AUTO_INCREMENT,
name VARCHAR(255) UNIQUE NOT NULL,
birth DATE NOT NULL
);
```
4. symptom_reports 테이블 생성
```sql
CREATE TABLE npcb_db.symptom_reports(
id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
child_name VARCHAR(255) NOT NULL,
symptom VARCHAR(255) NOT NULL,
description TEXT,
reported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (child_name) REFERENCES child(name) ON UPDATE CASCADE
);
```

<br/><hr/>

<h3>MySQL root 비밀번호 등록</h3>

* 프로그램을 실행한 직후, 터미널에 DB 비밀번호를 입력해야 진행됨.
* 한 번 입력한 비밀번호는 database/config.py 파일에 보관

<br/><hr/>
* Embedding Model: langchain_openai.OpenAIEmbeddings
* vectorstore: FAISS
* llm: langchain_openai.ChatOpenAI
* 대화 맥락 유지: langchain_community.chat_message_histories.ChatMessageHistory, langchain_core.runnables.history.RunnableWithMessageHistory
