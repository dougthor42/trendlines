#! /bin/bash

for run in {1..10}
do
curl -d '{"metric":"foo.bar", "value":'`shuf -i 1-100 -n 1`'}' -H "Content-Type: application/json" -X POST http://localhost:5001/api/v1/add;
sleep 0.1;
done;
sleep 1;
curl -d '{"metric":"foo.bar", "value":'`shuf -i 1-100 -n 1`', "time":'`date +%s`'}' -H "Content-Type: application/json" -X POST http://localhost:5001/api/v1/add;

for run in {1..5}
do
curl -d '{"metric":"baz", "value":'`shuf -i 1-100 -n 1`'}' -H "Content-Type: application/json" -X POST http://localhost:5001/api/v1/add;
sleep 0.3;
done;
