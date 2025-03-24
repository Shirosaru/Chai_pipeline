
import tempfile
from pathlib import Path
import numpy as np

from chai_lab.chai1 import run_inference

tmp_dir = Path(tempfile.mkdtemp())

# Prepare input fasta
example_fasta = '''>protein|name=Cetuximab heavy chain only
QVQLKQSGPGLVQPSQSLSITCTVSGFSLTNYGVHWVRQSPGKGLEWLGVIWSGGNTDYN
TPFTSRLSINKDNSKSQVFFKMNSLQSNDTAIYYCARALTYYDYEFAYWGQGTLVTVSAA
S
>protein|name=Cetuximab light chain
DILLTQSPVILSVSPGERVSFSCRASQSIGTNIHWYQQRTNGSPRLLIKYASESISGIPS
RFSGSGSGTDFTLSINSVESEDIADYYCQQNNNWPTTFGAGTKLELKRTVAAPSVFIFPP
SDEQLKSGTASVVCLLNNFYPREAKVQWKVDNALQSGNSQESVTEQDSKDSTYSLSSTLT
LSKADYEKHKVYACEVTHQGLSSPVTKSFNRGEC'''

fasta_path = tmp_dir / "example.fasta"
fasta_path.write_text(example_fasta)

# Generate structure
output_dir = tmp_dir / "outputs"
candidates = run_inference(
    fasta_file=fasta_path,
    output_dir=output_dir,
    num_trunk_recycles=3,
    num_diffn_timesteps=200,
    seed=42,
    device="cuda:0",
    use_esm_embeddings=True,
    msa_directory=Path(__file__).parent,
    use_msa_server=False,
)
cif_paths = candidates.cif_paths
scores = [rd.aggregate_score for rd in candidates.ranking_data]

# Load pTM, ipTM, pLDDTs and clash scores for sample 2
scores = np.load(output_dir.joinpath("scores.model_idx_2.npz"))
