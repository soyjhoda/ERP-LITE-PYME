def is_valid_float(value):
    """
    Verifica si una cadena de texto puede ser convertida a un número decimal (float).
    Esto es crucial para validar entradas de usuarios, como la tasa de cambio.
    """
    if isinstance(value, (int, float)):
        return True
    
    if not isinstance(value, str):
        return False

    # Reemplaza la coma (,) por punto (.) para asegurar que la conversión a float funcione
    cleaned_value = value.replace(',', '.')

    try:
        # Intenta convertir la cadena limpia a float
        float(cleaned_value)
        return True
    except ValueError:
        return False
