import os
import subprocess
from pathlib import Path
import shutil


def sanitize_name(name):
    # Function to sanitize the name (you can adjust this depending on your needs)
    return name.replace(" ", "_").replace("/", "_")

def split_fasta(fasta_path, output_dir):
    """
    Split a FASTA file into individual sequences and save them as separate files.
    Each sequence file name is sanitized before saving.
    """
    individual_fasta_files = []
    with open(fasta_path, 'r') as f:
        lines = f.readlines()
        seq_name = None
        seq_data = []
        
        for line in lines:
            if line.startswith('>'):
                if seq_name:  # If there's a sequence accumulated, write it out
                    sanitized_name = sanitize_name(seq_name)  # Sanitize the sequence name
                    seq_file_path = os.path.join(output_dir, f"{sanitized_name}.fasta")
                    with open(seq_file_path, 'w') as seq_file:
                        seq_file.write(f">{seq_name}\n")
                        seq_file.writelines(seq_data)
                    individual_fasta_files.append(seq_file_path)
                seq_name = line.strip().lstrip('>')
                seq_data = []
            else:
                seq_data.append(line)
        if seq_name:  # Write the last sequence
            sanitized_name = sanitize_name(seq_name)  # Sanitize the sequence name
            seq_file_path = os.path.join(output_dir, f"{sanitized_name}.fasta")
            with open(seq_file_path, 'w') as seq_file:
                seq_file.write(f">{seq_name}\n")
                seq_file.writelines(seq_data)
            individual_fasta_files.append(seq_file_path)

    return individual_fasta_files


def copy_files(src_dir, dest_dir, file_extension):
    # Function to copy all files with the given extension from src_dir to dest_dir recursively
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(file_extension):
                src_file = os.path.join(root, file)
                shutil.copy(src_file, dest_dir)
                print(f"Copied {src_file} to {dest_dir}")

def process_fasta_files(input_fasta_dir, cpu_num=12, package="jackhmm", database="uniref90", iterations=3):
    """
    Process each FASTA file in the given directory by running the A3M_TGT_Gen.sh script.
    
    :param input_fasta_dir: Directory containing the FASTA files to process
    :param cpu_num: Number of CPUs to use (default: 12)
    :param package: The package to use (default: "jackhmm")
    :param database: The database to use (default: "uniref90")
    :param iterations: The number of iterations to run (default: 3)
    :param final_output_dir: Directory where the copied .a3m files and input .fasta files will be stored
    """
    
    # Ensure the input directory exists
    if not os.path.isdir(input_fasta_dir):
        print(f"Error: The directory {input_fasta_dir} does not exist.")
        return
    
    # Process each FASTA file in the input directory
    for fasta_file in os.listdir(input_fasta_dir):
        if fasta_file.endswith(".fasta"):  # Only process .fasta files
            fasta_path = os.path.join(input_fasta_dir, fasta_file)

            # Extract the base name of the FASTA file (without extension)
            base_name = os.path.splitext(fasta_file)[0]

            # Create the final output directory as the basename + '_final_output'
            final_output_dir = os.path.join(input_fasta_dir, f"{base_name}_final_output")
            
            # Ensure the final output directory exists
            os.makedirs(final_output_dir, exist_ok=True)

            # Create the output directory based on the FASTA file name
            output_dir = os.path.join(input_fasta_dir, f"{sanitize_name(base_name)}_out")
            os.makedirs(output_dir, exist_ok=True)

            # Split the input FASTA file into individual FASTA files
            individual_fasta_files = split_fasta(fasta_path, output_dir)
            
            # Process each individual FASTA file
            for individual_fasta in individual_fasta_files:
                # Extract the individual sequence's name from the file name
                sequence_name = os.path.splitext(os.path.basename(individual_fasta))[0]

                # Create a directory for the sequence under the final output directory
                sequence_output_dir = os.path.join(final_output_dir, sanitize_name(sequence_name))
                os.makedirs(sequence_output_dir, exist_ok=True)

                # Construct the command to run the A3M_TGT_Gen.sh script
                command = [
                    "/home2/TGT_Package/A3M_TGT_Gen.sh",
                    "-c", str(cpu_num),        # Set CPU cores to 12
                    "-i", individual_fasta,    # Input individual FASTA file
                    "-o", sequence_output_dir, # Output directory
                    "-h", package,             # Package (e.g., jackhmm)
                    "-d", database,            # Database (e.g., uniref90)
                    "-n", str(iterations)      # Number of iterations (default: 3)
                ]
                # Print the command for debugging
                print("Running command: {}".format(" ".join(command)))            

                # Run the shell script
                try:
                    subprocess.run(command, check=True)
                    print(f"Successfully processed {individual_fasta} and saved results to {sequence_output_dir}.")
                except subprocess.CalledProcessError as e:
                    print(f"Error processing {individual_fasta}: {e}")
            
            # After processing, copy .a3m files and the original .fasta file to the final output directory
            copy_files(output_dir, final_output_dir, ".a3m")
            shutil.copy(fasta_path, final_output_dir)  # Copy the original .fasta file to the final output directory



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
    # Example usage:
    #final_output_dir="./TGT_output"
    #process_fasta_files(input_fasta_dir=".", final_output_dir=final_output_dir)
    process_fasta_files(input_fasta_dir=".")


    #input_dir = Path(".")  # Replace this with your input directory
    input_dir = final_output_dir  # Replace this with your input directory
    process_fasta_files(input_dir)
