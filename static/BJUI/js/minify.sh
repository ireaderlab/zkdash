###########################################
# 摘    要: minify.sh
# 创 建 者: WangLichao
# 创建日期: 2015-06-02
###########################################
#!/bin/bash

rm bjui-all.js && touch bjui-all.js
for js in `ls bjui-*.js|grep -v bjui-all.js|grep -v bjui-slidebar.js`;do
    echo $js "begin minify";
    java -jar yuicompressor-2.4.8.jar $js --charset utf-8 --type js >> bjui-all.js
done
