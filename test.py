import requests
from bs4 import BeautifulSoup
from fpdf import FPDF


def create_flashcards(data):
    def setup_pdf():
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.add_font(
            "DejaVu", "", "/usr/share/fonts/TTF/DejaVuSansCondensed.ttf", uni=True
        )
        pdf.set_font("DejaVu", "", 10)

        pdf.add_page()
        pdf.set_xy(0, 0)
        pdf.cell(0, 10, "Page 1", 0, 1, "C")
        return pdf

    def add_flashcards(pdf, side, is_back=False):
        # Flashcard dimensions and positioning
        card_width = 95
        card_height = 45
        x_start = 10
        y_start = 10
        x_space = 5
        y_space = 10
        shift_left_for_back = 5 if is_back else 0  # Shift left by 5mm for backside

        # Font settings
        font_size = 16
        pdf.set_font("DejaVu", "", font_size)
        line_height = pdf.font_size * 2.5  # Updated for better text centering
        page = 1
        count = 0
        for i in range(len(data)):
            if count % 10 == 0 and count != 0:
                page += 1
                pdf.add_page()  # Add a new page for the next set of flashcards
                pdf.set_font("DejaVu", "", 10)
                pdf.set_xy(0, 0)
                pdf.cell(0, 10, f"Page {page}", 0, 1, "C")
                pdf.set_font("DejaVu", "", font_size)

            # Calculate position
            row = (count // 2) % 5
            col = count % 2

            # Flip column positions for backside pairs
            if is_back:
                col = 1 - col  # 0 becomes 1, 1 becomes 0

            x = x_start + (card_width + x_space) * col - shift_left_for_back
            y = y_start + (card_height + y_space) * row

            # Draw box
            pdf.set_xy(x, y)
            pdf.cell(card_width, card_height, border=1)

            # Add "french" text in italics and muted grey color
            pdf.set_font("DejaVu", "", 12)  # Smaller font size for the "french" label
            pdf.set_text_color(169, 169, 169)  # Muted grey color
            pdf.set_xy(
                x + 2, y + 2
            )  # Position the "french" text slightly inside the top-left corner
            pdf.cell(0, 10, "french", 0, 0)
            pdf.set_text_color(0, 0, 0)  # Reset text color to black for main text
            pdf.set_font(
                "DejaVu", "", font_size
            )  # Reset font to original size and remove italics

            # Determine text to display
            text = data[i][side]

            # Calculate number of lines (rough estimate)
            num_lines = max(1, len(text) / (card_width / 2))  # Estimate number of lines

            # Adjust y to vertically center the text block, considering the number of lines
            adjusted_y = (
                y + (card_height - (num_lines * line_height)) / 2
            )  # Centering the text block vertically

            pdf.set_xy(x, adjusted_y)
            # Use multi_cell for text wrapping and center alignment, adjusting for the correct line height
            pdf.multi_cell(card_width, line_height, text, 0, "C")

            count += 1

    # Create PDF for fronts
    pdf_front = setup_pdf()
    add_flashcards(pdf_front, side=0, is_back=False)
    pdf_front.output("french-flashcards_front.pdf")

    # Create PDF for backs
    pdf_back = setup_pdf()
    add_flashcards(pdf_back, side=1, is_back=True)
    pdf_back.output("french-flashcards_back.pdf")


url = "https://vocab.chat/blog/most-common-french-words.html"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")
main_list = soup.find(id="main-list")

items = main_list.find_all("li")
data = []
for item in items:
    vocab = item.find(class_="vocab")
    pos = item.find(class_="pos")
    definition = item.find(class_="definition")
    # Extract text and add it to the list, handling potential None values
    data.append(
        [
            vocab.text if vocab else "",
            pos.text if pos else "",
            definition.text if definition else "",
        ]
    )

data = [[x[0], f"{x[1]}\n{x[2]}"] for x in data if len(x) > 2]
create_flashcards(data)
