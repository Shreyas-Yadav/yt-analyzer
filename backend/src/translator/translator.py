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
                content = f.read()
            
            # Split by the header separator
            parts = content.split("=" * 80)
            
            if len(parts) >= 2:
                # Extract header and main text
                header = parts[0] + "=" * 80
                main_text = parts[1].strip()
                
                # Translate the main text content
                translator = GoogleTranslator(source='auto', target=target_lang)
                
                # Split into paragraphs to handle better
                raw_paragraphs = [p.strip() for p in main_text.split('\n') if p.strip()]
                
                # Further split long paragraphs if needed
                paragraphs = []
                MAX_CHUNK_SIZE = 4500
                
                for p in raw_paragraphs:
                    if len(p) <= MAX_CHUNK_SIZE:
                        paragraphs.append(p)
                    else:
                        # Split by sentences (simple approximation)
                        sentences = p.replace('. ', '.|').replace('? ', '?|').replace('! ', '!|').split('|')
                        current_chunk = ""
                        
                        for sentence in sentences:
                            # If a single sentence is too long, force split it
                            if len(sentence) > MAX_CHUNK_SIZE:
                                # Split by character count
                                for i in range(0, len(sentence), MAX_CHUNK_SIZE):
                                    sub_chunk = sentence[i:i+MAX_CHUNK_SIZE]
                                    if len(current_chunk) + len(sub_chunk) < MAX_CHUNK_SIZE:
                                        current_chunk += sub_chunk
                                    else:
                                        if current_chunk:
                                            paragraphs.append(current_chunk.strip())
                                        current_chunk = sub_chunk
                            else:
                                if len(current_chunk) + len(sentence) < MAX_CHUNK_SIZE:
                                    current_chunk += sentence + " "
                                else:
                                    if current_chunk:
                                        paragraphs.append(current_chunk.strip())
                                    current_chunk = sentence + " "
                                
                        if current_chunk:
                            paragraphs.append(current_chunk.strip())
                
                translated_paragraphs = []
                batch_size = 50
                
                # Process in batches
                for i in range(0, len(paragraphs), batch_size):
                    batch = paragraphs[i:i+batch_size]
                    try:
                        results = translator.translate_batch(batch)
                        translated_paragraphs.extend(results)
                    except Exception as e:
                        print(f"Error translating batch {i}: {e}")
                        # Fallback: keep original for this batch
                        translated_paragraphs.extend(batch)
                
                # Reconstruct the file
                translated_content = header + "\n\n" + "\n".join(translated_paragraphs) + "\n"
            else:
                # Fallback: translate entire content
                translator = GoogleTranslator(source='auto', target=target_lang)
                translated_content = translator.translate(content)

            with open(new_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
                
            print(f"Translation saved to: {new_path}")
            return new_path

        except Exception as e:
            print(f"Error during transcript translation: {e}")
            raise e
