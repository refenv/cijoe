[[ -f "main.zip" ]] && rm main.zip
[[ -d "cijoe-pkg-example-main" ]] && rm -r "cijoe-pkg-example-main"
wget https://github.com/refenv/cijoe-pkg-example/archive/refs/heads/main.zip
unzip main.zip
ls cijoe-pkg-example-main
