"""HTTP protection tests use synthetic secrets in a disposable directory."""
import functools
import http.server
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import urlopen
from urllib.error import HTTPError
from serve_site import AtlasHandler


class PreviewProtection(unittest.TestCase):
    def test_http_boundaries(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root=Path(directory)
            fixtures=['index.html','.env','.git/config','cad/private/secret.FCStd','cad/table-node-pair_freecad_v0.1/index.html','assets/legacy.glb']
            for name in fixtures:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('synthetic fixture')
            (root/'alias').symlink_to(root/'cad/private',target_is_directory=True)
            (root/'secret-alias').symlink_to(root/'.env')
            (Path(outside)/'escape.txt').write_text('synthetic outside')
            (root/'escape').symlink_to(outside,target_is_directory=True)
            (root/'landing').mkdir();(root/'landing/index.html').symlink_to(Path(outside)/'escape.txt')
            (root/'secret-index').mkdir();(root/'secret-index/index.html').symlink_to(root/'.env')
            for private in [False,True]:
                handler=functools.partial(AtlasHandler,directory=directory,private_cad=private)
                server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                def status(path, method='GET'):
                    from urllib.request import Request
                    try:
                        with urlopen(Request(f'http://127.0.0.1:{server.server_port}{path}',method=method)) as response:return response.status
                    except HTTPError as e:
                        code=e.code;e.close();return code
                try:
                    for path in ['/index.html','/assets/legacy.glb']:self.assertEqual(status(path),200)
                    for path in ['/.env','/%2eenv','/.git/config','/secret-alias','/escape/escape.txt','/assets/','/landing/','/secret-index/']:
                        for method in ['GET','HEAD']:self.assertEqual(status(path,method),404,(path,private,method))
                    for path in ['/cad/private/secret.FCStd','/cad%2fprivate/secret.FCStd','/alias/secret.FCStd','/cad/table-node-pair_freecad_v0.1/index.html']:
                        self.assertEqual(status(path),200 if private else 404,(path,private))
                finally:
                    server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
