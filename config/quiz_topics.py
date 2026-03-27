QUIZ_TOPICS = {
    # Podstawy Programowania
    "Variables & Data Types": {
        "description": "Zmienne, typy danych, konwersje",
        "icon": "📦",
        "difficulty_levels": ["easy", "medium", "hard"]
    },
    "Loops & Conditionals": {
        "description": "Pętle, warunki, instrukcje sterujące",
        "icon": "🔄",
        "difficulty_levels": ["easy", "medium", "hard"]
    },
    "Functions & Methods": {
        "description": "Funkcje, metody, parametry, return",
        "icon": "⚙️",
        "difficulty_levels": ["easy", "medium", "hard"]
    },

    # Języki Programowania
    "Python": {
        "description": "Język Python, biblioteki, Django/FastAPI",
        "icon": "🐍",
        "difficulty_levels": ["easy", "medium", "hard"]
    },
    "PHP": {
        "description": "Język PHP, superglobale, sesje",
        "icon": "🐘",
        "difficulty_levels": ["easy", "medium", "hard"]
    },
    "SQL": {
        "description": "Język SQL, zapytania, optymalizacja",
        "icon": "🗄️",
        "difficulty_levels": ["easy", "medium", "hard"]
    },

    # Programowanie Obiektowe
    "OOP": {
        "description": "Klasy, dziedziczenie, polimorfizm, enkapsulacja",
        "icon": "🎯",
        "difficulty_levels": ["easy", "medium", "hard"]
    },
    "Design Patterns": {
        "description": "Wzorce projektowe, best practices",
        "icon": "🏗️",
        "difficulty_levels": ["medium", "hard"]
    },

    # Frameworki
    "Yii Framework": {
        "description": "Framework Yii, MVC, ActiveRecord",
        "icon": "🎪",
        "difficulty_levels": ["easy", "medium", "hard"]
    },

    # Web Services
    "REST API": {
        "description": "REST API, HTTP, komunikacja sieciowa",
        "icon": "🌐",
        "difficulty_levels": ["easy", "medium", "hard"]
    },

    # Narzędzia
    "Git": {
        "description": "Kontrola wersji, branching, merging",
        "icon": "🔗",
        "difficulty_levels": ["easy", "medium", "hard"]
    },
    "Docker": {
        "description": "Konteneryzacja, obrazy, compose",
        "icon": "🐳",
        "difficulty_levels": ["easy", "medium", "hard"]
    },

    # Bazy Danych
    "Databases": {
        "description": "Bazy danych, normalizacja, ACID",
        "icon": "🗂️",
        "difficulty_levels": ["easy", "medium", "hard"]
    },

    # Testing
    "Unit Testing": {
        "description": "Testy jednostkowe, mocking, TDD",
        "icon": "✅",
        "difficulty_levels": ["easy", "medium", "hard"]
    },

    # Biblioteki
    "Pydantic": {
        "description": "Walidacja danych, modele, serializacja",
        "icon": "📋",
        "difficulty_levels": ["easy", "medium", "hard"]
    },
}


def get_available_topics():
    """Zwraca listę dostępnych tematów"""
    return list(QUIZ_TOPICS.keys())


def get_topic_info(topic):
    """Zwraca informacje o danym temacie"""
    return QUIZ_TOPICS.get(topic, None)


def print_topics_menu():
    """Wyświetla menu z dostępnymi tematami"""
    print("\n📚 Dostępne tematy do quizu:\n")
    for i, (topic, info) in enumerate(QUIZ_TOPICS.items(), 1):
        icon = info.get("icon", "")
        desc = info.get("description", "")
        print(f"{i:2d}. {icon} {topic:<25} — {desc}")
    print(f"\n{len(QUIZ_TOPICS) + 1:2d}. 🎲 Losowy temat\n")
