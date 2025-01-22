import fitz  # PyMuPDF
import os
from rich.console import Console
from rich.text import Text
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initialize Rich console
console = Console()

def split_pdf(input_pdf_path, output_folder, pages_per_split=10):
    # Open the PDF file
    pdf_document = fitz.open(input_pdf_path)
    total_pages = pdf_document.page_count

    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Split the PDF into smaller PDFs
    for start_page in range(0, total_pages, pages_per_split):
        end_page = min(start_page + pages_per_split - 1, total_pages - 1)
        split_pdf = fitz.open()
        split_pdf.insert_pdf(pdf_document, from_page=start_page, to_page=end_page)

        # Save the split PDF
        output_path = os.path.join(output_folder, f"part_{start_page // pages_per_split + 1}.pdf")
        split_pdf.save(output_path)
        split_pdf.close()

    # Close the original PDF file
    pdf_document.close()

def search_texts_in_pdf(pdf_path, search_texts, output_file):
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    found_all = True
    found_lines = []

    # Search for all texts in each page
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text = page.get_text("text")
        lines = text.split('\n')
        for line_num, line in enumerate(lines):
            if all(search_text in line for search_text in search_texts):
                found_lines.append(f"Part {page_num + 1}, Line {line_num + 1}: {line.strip()}")

    # Close the PDF file
    pdf_document.close()

    # Write found lines to output file
    if found_lines:
        with open(output_file, 'a') as f:
            f.write(f"found in {os.path.basename(pdf_path)}\n")
            for line in found_lines:
                f.write(line + '\n')
            f.write('\n')

    return bool(found_lines)

def process_pdf(pdf_path, search_texts, output_file):
    if search_texts_in_pdf(pdf_path, search_texts, output_file):
        console.print(Text(f"found in {os.path.basename(pdf_path)}", style="bold green"))
    else:
        os.remove(pdf_path)
        console.print(Text(f"Not found in {os.path.basename(pdf_path)}. Deleted.", style="bold red"))

def main(input_pdf_path, output_folder, search_texts, pages_per_split=10):
    # Output file path
    output_file = "output.txt"

    # Clear the output file if it exists
    if os.path.exists(output_file):
        os.remove(output_file)

    # Split the PDF
    split_pdf(input_pdf_path, output_folder, pages_per_split)

    # Get list of split PDF files
    pdf_files = [os.path.join(output_folder, filename) for filename in os.listdir(output_folder) if filename.endswith(".pdf")]

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_pdf, pdf_path, search_texts, output_file) for pdf_path in pdf_files]
        for future in as_completed(futures):
            future.result()  # Ensure any exceptions are raised

if __name__ == "__main__":
    # Ask the user for the PDF file path
    input_pdf_path = input("Enter the path to the PDF file: ").strip()

    # Validate the PDF file path
    if not os.path.exists(input_pdf_path):
        console.print(Text("The provided PDF file path does not exist. Please check the path and try again.", style="bold red"))
        exit()

    # Output folder
    output_folder = "output"

    # Ask the user for the candidate's name, Parent's name
    candidate_name = input("Enter the candidate's name: ").upper()
    first_parent = input("Enter the 1st Parent name: ").upper()
    second_parent = input("Enter the 2nd Parent name: ").upper()

    # Filter out empty strings
    search_texts = [name for name in [candidate_name, first_parent, second_parent] if name]

    # Call the main function
    main(input_pdf_path, output_folder, search_texts)