import os
from deep_translator import GoogleTranslator

class Translator:
    def __init__(self):
        pass

    def translate_text(self, text, target_lang):
        """
        Translates a single string to the target language.
        """
        try:
            # Use GoogleTranslator from deep-translator
            # It handles chunking automatically for longer texts usually, 
            # but for very large texts we might need to be careful.
            # For now, we assume reasonable segment lengths.
            translator = GoogleTranslator(source='auto', target=target_lang)
            return translator.translate(text)
        except Exception as e:
            print(f"Error translating text: {e}")
            return text # Return original text on failure

    def translate_transcript(self, transcript_path, target_lang):
        """
        Reads a transcript file, translates it, and saves it to a new file.
        Returns the path to the translated transcript.
        """
        if not os.path.exists(transcript_path):
            raise FileNotFoundError(f"Transcript file not found: {transcript_path}")

        try:
            # Construct new filename
            directory = os.path.dirname(transcript_path)
            filename = os.path.basename(transcript_path)
            name, ext = os.path.splitext(filename)
            
            new_filename = f"{name}_{target_lang}{ext}"
            new_path = os.path.join(directory, new_filename)
            
            print(f"Translating {transcript_path} to {target_lang}...")
            
            with open(transcript_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            translated_lines = []
            text_to_translate = []
            line_indices_map = [] # Tuples of (line_index, type, extra_data)
            
            # Types: 
            # 0: Plain line (header/separator/empty) - No translation
            # 1: Timestamped line - Translate text part
            # 2: Full text line - Translate whole line
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    line_indices_map.append((i, 0, None))
                    continue
                
                if line.startswith("Transcript:") or line.startswith("=") or line.startswith("-") or line == "Full Text:" or line == "Timestamped Segments:":
                    line_indices_map.append((i, 0, None))
                    continue
                
                # Check for timestamp: [0.00s - 5.00s] Text
                if line.startswith("[") and "s]" in line:
                    try:
                        parts = line.split("] ", 1)
                        if len(parts) == 2:
                            timestamp_part = parts[0] + "] "
                            text_part = parts[1]
                            text_to_translate.append(text_part)
                            line_indices_map.append((i, 1, timestamp_part))
                        else:
                            line_indices_map.append((i, 0, None))
                    except:
                        line_indices_map.append((i, 0, None))
                else:
                    # Assume it's a text line (e.g. in Full Text section)
                    # Skip very long lines to avoid errors, or try to translate them
                    if len(line) < 4500:
                        text_to_translate.append(line)
                        line_indices_map.append((i, 2, None))
                    else:
                        # Too long, keep original
                        line_indices_map.append((i, 0, None))

            # Perform batch translation
            translator = GoogleTranslator(source='auto', target=target_lang)
            translated_texts = []
            
            # Chunking to avoid limits (e.g. 50 items per batch)
            batch_size = 50
            for i in range(0, len(text_to_translate), batch_size):
                batch = text_to_translate[i:i+batch_size]
                try:
                    results = translator.translate_batch(batch)
                    translated_texts.extend(results)
                    print(f"Translated batch {i//batch_size + 1}/{(len(text_to_translate)-1)//batch_size + 1}")
                except Exception as e:
                    print(f"Error translating batch {i}: {e}")
                    # Fallback: keep original for this batch
                    translated_texts.extend(batch)

            # Reconstruct lines
            translation_idx = 0
            for i, type, extra in line_indices_map:
                original_line = lines[i]
                if type == 0:
                    translated_lines.append(original_line)
                elif type == 1: # Timestamped
                    timestamp_part = extra
                    if translation_idx < len(translated_texts):
                        translated_text = translated_texts[translation_idx]
                        translated_lines.append(f"{timestamp_part}{translated_text}\n")
                        translation_idx += 1
                    else:
                        translated_lines.append(original_line)
                elif type == 2: # Full text
                    if translation_idx < len(translated_texts):
                        translated_text = translated_texts[translation_idx]
                        translated_lines.append(f"{translated_text}\n")
                        translation_idx += 1
                    else:
                        translated_lines.append(original_line)

            with open(new_path, 'w', encoding='utf-8') as f:
                f.writelines(translated_lines)
                
            print(f"Translation saved to: {new_path}")
            return new_path

        except Exception as e:
            print(f"Error during transcript translation: {e}")
            raise e
