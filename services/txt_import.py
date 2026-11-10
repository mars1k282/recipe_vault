import re


def parse_txt_recipe(file_path: str) -> dict | None:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        recipe = {
            'name': '',
            'description': '',
            'category': '',
            'ingredients': [],
            'steps': []
        }

        name_match = re.search(r'Название:\s*(.*?)(?=\n|Описание:|Категория:|Ингредиенты:|$)', text, re.IGNORECASE)
        if name_match:
            recipe['name'] = name_match.group(1).strip()

        desc_match = re.search(r'Описание:\s*(.*?)(?=\nКатегория:|\nИнгредиенты:|\nШаги:|$)', text,
                               re.IGNORECASE | re.DOTALL)
        if desc_match:
            recipe['description'] = desc_match.group(1).strip()

        cat_match = re.search(r'Категория:\s*(.*?)(?=\n|Ингредиенты:|$)', text, re.IGNORECASE)
        if cat_match:
            recipe['category'] = cat_match.group(1).strip()

        ing_match = re.search(r'Ингредиенты:\s*(.*?)(?=Шаги:|$)', text, re.IGNORECASE | re.DOTALL)
        if ing_match:
            ing_text = ing_match.group(1).strip()
            recipe['ingredients'] = [
                re.sub(r'^[-*•]\s*', '', line).strip()
                for line in ing_text.split('\n')
                if line.strip()
            ]

        steps_match = re.search(r'Шаги(?: приготовления)?:\s*(.*)', text, re.IGNORECASE | re.DOTALL)
        if steps_match:
            steps_text = steps_match.group(1).strip()
            recipe['steps'] = [
                re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                for line in steps_text.split('\n')
                if line.strip()
            ]

        if not recipe['name']:
            return None

        return recipe
    except Exception as e:
        print(e)
        return None
