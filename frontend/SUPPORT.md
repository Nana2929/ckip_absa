## REQUEST and CHECKBOX 
- issue: Flask request does not get the checkbox value

https://stackoverflow.com/questions/67477646/cant-have-the-value-of-a-check-box-from-html-using-flask
https://social.msdn.microsoft.com/Forums/en-US/e0f1f4a7-e1fa-43c1-8022-9090a4804a7b/requestform-for-a-checkbox?forum=aspwebforms
https://stackoverflow.com/questions/31859903/get-the-value-of-a-checkbox-in-flask

## Clearing log file
- issue: invalid chars appear after doing file.truncate(0)

https://stackoverflow.com/questions/48862654/strange-characters-in-the-begining-of-the-file-after-writing-in-python
Solution: 
- 要把logger改成module level logger，然後每次init module並使用完後都要 removeHandler，才有辦法每次都完全清空檔案。
- See [Advanced Logger Tutorial](https://docs.python.org/3/howto/logging.html#advanced-logging-tutorial)
- Check my local/logging-practice 
- `main.py` simulates `demo.py` (executor); `f1.py` simulates `DepTree.py` (module)
- Initialize module-level logger in `DepTree.py` (by `self.logger = logging.getLogger(__name__)`), add formatter, handler (specify logfile path) etc. 
- Access the logfile in `demo.py` simply by its name 
- Clear log file when done using the current instantialized `DepTree` object by `self.logger.removeHandler(self.file_handler)`, so the next instantialized `DepTree` object gets a new file handler (i.e. a new, clean file). 

