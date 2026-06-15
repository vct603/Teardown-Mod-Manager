"""
用主控台模式啟動 GUI，捕捉所有背景執行緒的錯誤
"""
import sys
import threading
import traceback

# Monkey-patch Thread 以捕捉背景例外
_orig_thread_run = threading.Thread.run
def _patched_thread_run(self):
    try:
        _orig_thread_run(self)
    except Exception:
        print(f"\n!!! THREAD ERROR in {self.name} !!!", file=sys.stderr)
        traceback.print_exc()
threading.Thread.run = _patched_thread_run

# 啟動 GUI
from main import App
app = App()
app.mainloop()
