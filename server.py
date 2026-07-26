import os
import re
import mimetypes
from http.server import SimpleHTTPRequestHandler, test


class RangeRequestHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()

        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None

        range_header = self.headers.get('Range')
        if not range_header:
            return super().send_head()

        # Разбираем заголовок Range (запрос конкретного куска видео)
        match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if not match:
            return super().send_head()

        fs = os.fstat(f.fileno())
        file_len = fs.st_size
        start, end = match.groups()
        start = int(start)
        end = int(end) if end else file_len - 1

        if start >= file_len:
            self.send_error(416, "Requested Range Not Satisfiable")
            f.close()
            return None

        # Отправляем правильный статус 206 (Partial Content)
        self.send_response(206)
        self.send_header('Content-type', ctype)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Range', f'bytes {start}-{end}/{file_len}')
        self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
        self.end_headers()

        f.seek(start)
        return f


if __name__ == '__main__':
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Запускаем сервер с поддержкой перемотки на порту {port}...")
    test(HandlerClass=RangeRequestHandler, port=port)