from pathlib import Path
import nbformat
from nbclient import NotebookClient

infile = Path('/mnt/data/LeadFlowML_Project/notebooks/LeadFlowML_demo.ipynb')
outfile = Path('/mnt/data/LeadFlowML_Project/notebooks/LeadFlowML_demo_executed.ipynb')
nb = nbformat.read(infile, as_version=4)
client = NotebookClient(nb, timeout=300, kernel_name='python3', resources={'metadata': {'path': str(infile.parent)}})
client.execute()
nbformat.write(nb, outfile)
print(outfile)
