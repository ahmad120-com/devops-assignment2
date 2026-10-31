# Student Records - CSC418 Assignment 2

Simple Flask web app that stores student records in MySQL.

| | Part I | Part II |
|---|---|---|
| How it runs | Image from Docker Hub (`ahmadkhan0901/student-records:v1`) | Jenkins pipeline, code mounted as a volume |
| Compose file | `docker-compose.yml` | `part2/docker-compose.yml` |
| Web | host `8000` -> container `5000` (`p1-web`) | host `9090` -> container `5000` (`p2-web`) |
| MySQL | host `3307` -> container `3306` (`p1-db`) | host `3308` -> container `3306` (`p2-db`) |
| DB volume | `p1_db_data` | `p2_db_data` |

Part I: `docker compose -p part1 up -d`
Part II: started by Jenkins on every push to `main` (see `Jenkinsfile`).
