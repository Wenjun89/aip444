# File System (fs)

## fs.readFileSync(path[, options])
- `path` <string> | <Buffer> | <URL> | <integer>
- `options` <string> | <Object>
- Returns: <string> | <Buffer>

Synchronously reads the entire contents of a file. 

Example:
```js
const fs = require('node:fs');
const data = fs.readFileSync('/file.txt', 'utf8');
console.log(data);