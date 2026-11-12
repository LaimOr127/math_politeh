"""Compile all canonical examples and verify the final project's HTTP boundary."""
import json, os, subprocess, tempfile, time, urllib.request, urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
COURSE=json.loads((ROOT/'java-course/content/course.json').read_text(encoding='utf-8'))
def run(args,cwd):
    return subprocess.run(args,cwd=cwd,capture_output=True,text=True,encoding='utf-8',timeout=40,check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)).stdout.strip()
def request(path,method='GET'):
    try:
        with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8090'+path,method=method),timeout=3) as r:return r.status,r.read().decode('utf-8')
    except urllib.error.HTTPError as e:return e.code,e.read().decode('utf-8')

def verify():
    (ROOT/'.build/java-tests').mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT/'.build/java-tests') as work:
        work=Path(work)
        for i,lesson in enumerate(COURSE['lessons']):
            folder=work/str(i+1);folder.mkdir()
            source=ROOT/f'java-course/examples/lesson-{i+1:02d}/Main.java'
            assert source.read_text(encoding='utf-8').strip()==lesson['code']
            run(['javac','--release','21','-encoding','UTF-8','-d',str(folder),str(source)],ROOT)
            if i<9: assert run(['java','-cp',str(folder),'Main'],ROOT)==lesson['stdout'],lesson['id']
            for extra in lesson.get('extraExamples',[]):
                p=ROOT/f'java-course/examples/lesson-{i+1:02d}'/extra['file']
                assert p.read_text(encoding='utf-8').strip()==extra['code']
                run(['javac','--release','21','-encoding','UTF-8','-d',str(folder),str(p)],ROOT)
                for name,value in extra.get('files',{}).items():(folder/name).write_text(value,encoding='utf-8')
                result=subprocess.run(['java','-cp',str(folder),p.stem],cwd=folder,input=extra['stdin'],text=True,encoding='utf-8',capture_output=True,timeout=10,check=True)
                assert result.stdout.strip()==extra['stdout']
                if p.stem=='ReadInput':
                    for invalid in ('','x 2','5 0','-1 5'):
                        invalid_run=subprocess.run(['java','-cp',str(folder),p.stem],cwd=folder,input=invalid,text=True,encoding='utf-8',capture_output=True,timeout=10,check=True)
                        assert invalid_run.stdout.strip()=='invalid'
                if p.stem=='ReadWeights':
                    for invalid in ('0\n','01\n','12\n2\n','x','','1'*101):
                        (folder/'weights.txt').write_text(invalid,encoding='utf-8')
                        assert run(['java','-cp',str(folder),p.stem],folder)=='invalid'
                    (folder/'weights.txt').unlink()
                    assert run(['java','-cp',str(folder),p.stem],folder)=='invalid'
        project=ROOT/'java-course/project'
        compiled=work/'project';compiled.mkdir()
        run(['javac','--release','21','-encoding','UTF-8','-d',str(compiled),*[str(p) for p in project.glob('*.java')]],ROOT)
        assert run(['java','-cp',str(compiled),'RoutePlannerTest'],ROOT)=='OK'
        # Never attach to or stop an existing server on this port.
        import socket
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',8090))
        proc=subprocess.Popen(['java','-cp',str(compiled),'Main'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:
            for _ in range(40):
                if proc.poll() is not None: raise RuntimeError(proc.stderr.read().decode('utf-8'))
                try:
                    if request('/')[0]==200:break
                except OSError:time.sleep(.1)
            else:raise RuntimeError('Java server did not start')
            assert request('/route?w=1')==(200,'{"cost":6,"path":"A-C-B-D"}')
            for w in (2,3,99): assert json.loads(request('/route?w='+str(w))[1])['cost']==7
            for query in ('','?w=0','?w=100','?w=01','?w=-1','?w=1&w=2','?w=1&x=2','?w=%31'):
                assert request('/route'+query)[0]==400,query
            assert request('/route?w=1','POST')[0]==405
            assert request('/missing')[0]==404
            assert request('/route/extra?w=1')[0]==404
            for asset in ('/app.js','/style.css'):assert request(asset)[0]==200
            assert run(['java','-cp',str(work/'10'),'Main'],ROOT)==COURSE['lessons'][9]['stdout']
        finally:
            proc.terminate();proc.wait(timeout=5)
    print('Java: 12 programs, 100 reference DAG comparisons, input/file/parser and HTTP checks passed')
if __name__=='__main__':verify()
