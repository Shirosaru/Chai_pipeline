import os
import subprocess
from pathlib import Path
import shutil

def process_fasta_files(input_dir):
    # Ensure input_dir is a Path object
    input_dir = Path(input_dir)

    # Step 1: Find the fasta file and a3m files in the input directory
    fasta_file = None
    a3m_files = []

    for file in input_dir.iterdir():
        if file.suffix == ".fasta":
            fasta_file = file
        elif file.suffix == ".a3m":
            a3m_files.append(file)

    if not fasta_file:
        raise FileNotFoundError("No .fasta file found in the input directory.")
    
    if not a3m_files:
        raise FileNotFoundError("No .a3m files found in the input directory.")

    # Step 2: Run chai-lab a3m-to-pqt for each a3m file
    try:
        print(f"Processing {a3m_files}...")
        
        for a3m_file in a3m_files:
            # Step 3: Create a new directory for each .a3m file
            a3m_dir = input_dir / a3m_file.stem
            a3m_dir.mkdir(parents=True, exist_ok=True)

            # Step 4: Move the a3m file into its respective directory and rename it to uniref90.a3m
            new_a3m_path = a3m_dir / "uniref90.a3m"
            shutil.move(a3m_file, new_a3m_path)

            # Step 5: Run chai-lab a3m-to-pqt for the renamed a3m file
            try:
                print(f"Running chai-lab a3m-to-pqt on {new_a3m_path}...")
                subprocess.run(["chai-lab", "a3m-to-pqt", str(a3m_dir)], check=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Error processing {new_a3m_path}: {str(e)}")

            # Step 6: Create an output directory based on the fasta file name (without the extension)
            output_dir = fasta_file.parent / f"{fasta_file.stem}_output"
            output_dir.mkdir(parents=True, exist_ok=True)  # Create the output directory

            # Step 7: Move the .pqt files to the output directory
            pqt_files = a3m_dir.glob("*.pqt")
            for pqt_file in pqt_files:
                shutil.move(pqt_file, output_dir / pqt_file.name)

            print(f"Moved .pqt files to {output_dir}")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error processing a3m files: {str(e)}")
    # Step 4: Modify the FASTA headers and write to the predict_with_msas.py script
    try:
        # Read the original FASTA content
        example_fasta = fasta_file.read_text()

        # Modify headers (all lines starting with '>')
        modified_fasta = []
        for line in example_fasta.splitlines():
            if line.startswith(">"):
                protein_name = line[1:]  # Remove '>' symbol to get the protein name
                #modified_fasta.append(f">name={protein_name}")
                modified_fasta.append(f">protein|name={protein_name}")
            else:
                modified_fasta.append(line)

        # Join the modified lines back into a single string
        modified_fasta_content = "\n".join(modified_fasta)

        # Create the predict_with_msas.py script
        predict_file_path = output_dir / "predict_with_msas.py"
        
        # Escape triple quotes and insert them correctly in the string
        predict_script = f"""
import tempfile
from pathlib import Path
import numpy as np

from chai_lab.chai1 import run_inference

tmp_dir = Path(tempfile.mkdtemp())

# Prepare input fasta
example_fasta = '''{modified_fasta_content}'''

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
"""
        predict_file_path.write_text(predict_script)
        
        # Step 5: Run the predict_with_msas.py script in the activated conda environment
        subprocess.run(["conda", "activate", "chai"], shell=True)  # Activate chai environment
        subprocess.run(["python", str(predict_file_path)], check=True)  # Run the script
        print(f"Prediction completed. Output saved in: {output_dir}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure any temporary directories or resources are cleaned up (if necessary)
        pass

if __name__ == "__main__":
    input_dir = Path(".")  # Replace this with your input directory
    process_fasta_files(input_dir)
