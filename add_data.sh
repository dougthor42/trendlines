#! /bin/bash

PORT=5000
URL="http://localhost:$PORT"
API="$URL/api/v1/data"

for run in {1..10}
do
curl -d '{"metric":"foo.bar", "value":'`shuf -i 1-100 -n 1`'}' -H "Content-Type: application/json" -X POST "$API";
sleep 0.1;
done;
sleep 1;
curl -d '{"metric":"foo.bar", "value":'`shuf -i 1-100 -n 1`', "time":'`date +%s`'}' -H "Content-Type: application/json" -X POST "$API";

for run in {1..5}
do
curl -d '{"metric":"baz", "value":'`shuf -i 1-100 -n 1`'}' -H "Content-Type: application/json" -X POST "$API";
sleep 0.3;
done;
