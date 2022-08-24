#!/bin/bash
# check if the server process is running

# VARIABLES
Port=2022
ParserPath="/share/home/nana2929/chyiin_ch_parser"
url_pre='https://ckip.iis.sinica.edu.tw/service/restaurant-absa'
session="server_process"

# RUN SERVER
tmux has-session -t $session 2>/dev/null
if [ $? -eq 0 ]; then
  echo "Server process is set-up."
else
  echo "Setting up server process..."
  cd $ParserPath
  bash run_server.sh $Port
fi

# RUN DEMO
# When demo.py is set up, uncomment the below lines (not tested 2022.8.8)
# echo "Setting up demo..."
# python3 ./demo.py --port $Port --url_pre $url_pre
# echo "Demo running at $url_pre."

