export PATH=$HOME/.local/bin:/afs/cern.ch/cms/lumi/brilconda-1.0.3/bin:$PATH
pip uninstall brilws
pip install --install-option="--prefix=$HOME/.local" brilws
