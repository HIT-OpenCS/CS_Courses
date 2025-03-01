const fs = require('fs');
const path = require('path');

// 读取config.json文件
const configFile = path.join(__dirname, 'config.json');
const configData = require(configFile);
let dl_link = "";
// 遍历路径数组
configData.paths.forEach((currentPath) => {
    const outputPath = path.join(currentPath, 'file.md');

    // 获取忽略列表
    const ignoreList = configData.ignore || [];

    // 递归获取文件和子文件夹信息
    function exploreDirectory(directoryPath, depth) {
        const files = fs.readdirSync(directoryPath);

        let result = '';
        for (const file of files) {
            // 检查是否在忽略列表中
            if (ignoreList.includes(file)) {
                continue;
            }

            const filePath = path.join(directoryPath, file);
            const stats = fs.statSync(filePath);

            if (stats.isDirectory()) {
                result += `**${file}**\n\n`;
                result += exploreDirectory(filePath, depth + 1);
            } else {
                result += `[${file}](https://gh.hitcs.cc/https://raw.githubusercontent.com/HIT-OpenCS/CS_Courses/main/${filePath})\n\n`.replace(/\\/g, "/");
            }
        }
        return result;
    }
    dl_link+=`![](https://gh.hitcs.cc/https://raw.githubusercontent.com/HIT-OpenCS/CS_Courses/main/`+outputPath+` ":include")\n\n`;
    
    // 写入文件
    const content = exploreDirectory(currentPath, 0);
    fs.writeFileSync(outputPath, content);

    console.log(`File generated successfully for path: ${currentPath}`);
});
fs.writeFileSync("./dl_link.md", dl_link.replace(/\\/g, "/"));

console.log('Script execution completed.');
