import os
import shutil
import subprocess

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

def process_fasta_files(input_fasta_dir, cpu_num=12, package="jackhmm", database="uniref90", iterations=3, final_output_dir="final_output"):
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
    
    # Ensure the final output directory exists
    os.makedirs(final_output_dir, exist_ok=True)

    # Process each FASTA file in the input directory
    for fasta_file in os.listdir(input_fasta_dir):
        if fasta_file.endswith(".fasta"):  # Only process .fasta files
            fasta_path = os.path.join(input_fasta_dir, fasta_file)

            # Extract the base name of the FASTA file (without extension)
            base_name = os.path.splitext(fasta_file)[0]

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

# Example usage:
process_fasta_files(input_fasta_dir=".", final_output_dir="./TGT_output")
