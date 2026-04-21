#!/usr/bin/expect -f
spawn git push origin HEAD:main
expect "Username"
send "Shiv-7303\r"
expect "Password"
send "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\r"
expect eof
