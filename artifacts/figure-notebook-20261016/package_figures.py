import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

root = Path(__file__).resolve().parents[2]
output = root / 'artifacts/figure-handoff-20261016'
output.mkdir(parents=True,exist_ok=True)
commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
raw = subprocess.check_output(['git','archive','--format=zip','--prefix=DeepFace-PAD/','HEAD'],cwd=root)
bundle = output / 'DeepFace-PAD-Figures-source.zip'
excluded = []
with zipfile.ZipFile(io.BytesIO(raw)) as source,zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as archive:
    for item in source.infolist():
        data = source.read(item.filename)
        if item.filename.endswith('.ipynb') and any(cell.get('outputs') for cell in json.loads(data).get('cells',[])):
            excluded.append(item.filename)
            continue
        archive.writestr(item,data)
    archive.writestr('DeepFace-PAD/SOURCE_COMMIT.txt',commit+'\n')
notebook = output / 'Face_PAD_Export_All_Figures_E0_E4.ipynb'
notebook.write_bytes(subprocess.check_output(['git','show','HEAD:notebooks/'+notebook.name],cwd=root))
guide = output / 'FIGURE_NOTEBOOK_GUIDE.md'
guide.write_bytes(subprocess.check_output(['git','show','HEAD:reports/FIGURE_NOTEBOOK_GUIDE.md'],cwd=root))
ready_zip = Path(shutil.make_archive(str(output/'DeepFace-PAD-20-Figures-Ready'),'zip',root_dir=root/'artifacts/figure-notebook-20261016/numeric-final'))
files = [bundle,notebook,guide,ready_zip]
metadata = {'figure_source_commit':commit,'experiment_source_commit':'525c80889106c06525f5b758e8725c8ac9cee856',
    'excluded_executed_notebooks':excluded,'ready_figure_scope':'20 actual numeric figures only; full 31 need notebook GPU inference/timing',
    'files':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files}}
(output/'package-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
with zipfile.ZipFile(bundle) as archive: archive.extractall(output/'source-check')
print(json.dumps(metadata,indent=2))
