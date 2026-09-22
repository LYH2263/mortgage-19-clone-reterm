# 15-mortgage（房贷月供）

Mortgage — 等额本息月供与逐期本金利息拆分

## 启动

```bash
docker compose up --build
```

| 入口 | 地址 |
| --- | --- |
| 前端 | http://localhost:4400 |
| API | http://localhost:9400 |

## 主链

贷额期限利率 → 等额本息还款表 → 利息合计

## 换期克隆对照

`POST /api/loans/{id}/term-clone`，入参 `new_months`（1~600 且不得与源期数相同）、`persist`（默认 false 只试算）、`keep_clone`（persist 时是否保留克隆档案）。两侧各跑等额本息，回包源/克隆月供、利息合计与月供差额；persist 时事务写入一条 `term_clone_compare` 对照记录（钉选源与克隆标识及两侧月供快照），克隆失败整体回滚不留半条档案。`PATCH /api/loans/{id}` 改利率不影响已落库的对照记录；`GET /api/history/{id}` 打开单条记录。

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。
