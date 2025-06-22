from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import get_db_connection

router = Router()

@router.callback_query(F.data.startswith("lecture_"))
async def view_lecture_material(callback: CallbackQuery):
    material_id = int(callback.data.split("_")[1])
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get material info
    cursor.execute("SELECT title, description FROM lecture_materials WHERE material_id = ?", (material_id,))
    material = cursor.fetchone()
    
    if not material:
        await callback.message.answer("Материал не найден.")
        return
    
    # Send material info
    await callback.message.answer(f"📚 {material[0]}\n\n{material[1] if material[1] else ''}")
    
    # Get content
    cursor.execute(
        "SELECT message, file_id, file_type FROM lecture_content WHERE material_id = ? ORDER BY order_num",
        (material_id,)
    )
    contents = cursor.fetchall()
    
    for content in contents:
        if content[0]:  # Text message
            await callback.message.answer(content[0])
        elif content[1]:  # File
            if content[2] == 'document':
                await callback.message.answer_document(content[1])
            elif content[2] == 'photo':
                await callback.message.answer_photo(content[1])
            elif content[2] == 'video':
                await callback.message.answer_video(content[1])
            elif content[2] == 'audio':
                await callback.message.answer_audio(content[1])
    
    conn.close()