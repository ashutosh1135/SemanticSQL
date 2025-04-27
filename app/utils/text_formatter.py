from typing import List, Dict

async def format_schema_text(schema_info: List[Dict]) -> str:
    """Format schema info into natural language text."""
    formatted_text = ""

    current_table = None
    for item in schema_info:
        table = f"{item['schema_name']}.{item['table_name']}"
        if table != current_table:
            if current_table is not None:
                formatted_text += "\n"
            formatted_text += f"Table {table} has columns:\n"
            current_table = table
        
        column_line = f" - {item['column_name']} ({item['data_type']})"
        if item['is_primary_key']:
            column_line += " [Primary Key]"
        if item['is_foreign_key']:
            column_line += f" [Foreign Key to {item['foreign_table']}.{item['foreign_column']}]"
        
        formatted_text += column_line + "\n"

    return formatted_text.strip()

async def save_text_to_file(text: str, file_path: str):
    """Save formatted text to file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
