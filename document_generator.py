from docx import Document
from docx.shared import Cm
from PIL import Image
from io import BytesIO
import os
from bot_instance import bot


async def generate_document(user_id, user_info):
    doc = Document("template.docx")

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if "[дата]" in cell.text:
                    cell.text = cell.text.replace("[дата]", user_info["date"])
                if "[адрес]" in cell.text:
                    cell.text = cell.text.replace("[адрес]", user_info["address"])
                if "[вставка]" in cell.text:
                    cell.text = ""
                    for photo_id in user_info["photos"]:
                        photo = await bot.download(file=await bot.get_file(photo_id))
                        image = Image.open(BytesIO(photo.read()))

                        width_cm = 18
                        height_cm = 13.5
                        dpi = 96
                        width_px = int((width_cm / 2.54) * dpi)
                        height_px = int((height_cm / 2.54) * dpi)
                        image.thumbnail((width_px, height_px))

                        temp_image_path = f"temp_{user_id}_{photo_id}.jpg"
                        image.save(temp_image_path)

                        paragraph = cell.add_paragraph()
                        paragraph.alignment = 1
                        run = paragraph.add_run()
                        run.add_picture(
                            temp_image_path, width=Cm(width_cm), height=Cm(height_cm)
                        )

                        os.remove(temp_image_path)

    date = user_info["date"]
    address = user_info["address"]
    output_path = f"Отчет о проведенном ТО-{date}  {address}.docx"
    doc.save(output_path)
    return output_path
