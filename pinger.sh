# This is pinger service for GithubChatworkBot.
# It pings bot url every minute and sends message to designated Chatwork room if response is different from expected.

# real
chatworkkey="d0453c4....192e44a2dc9"
room="40...94"
# test
#chatworkkey="40339.....4e05e52412c7"
#room="36...21"

status="ok"
while true
do
    content=$(curl -L --max-time 30 localhost/index.py)
    if [ "$content" == "ok" ]; then
        echo "ok"
        if [ "$status" == "ng" ]; then
            curl -i \
            -H "X-ChatWorkToken: $chatworkkey" \
            --max-time 30 \
            -X POST --data 'body=(roger)' "https://api.chatwork.com/v1/rooms/$room/messages"
        fi
        status="ok"
        sleep 60
    else
        echo "ng"		
            if [ "$status" == "ok" ]; then
                curl -i \
                -H "X-ChatWorkToken: $chatworkkey" \
                --max-time 30 \
                -X POST --data $'body=[To:1550555]\n|-)' "https://api.chatwork.com/v1/rooms/$room/messages"
            fi
            status="ng"        
            sleep 60
    fi
done
