# Technical/Programming Example

This example demonstrates a code snippet card template ideal for memorizing programming concepts, syntax, and best practices.

## Features

- **Four fields**: Concept name, Code snippet, Programming language, and Explanation
- **Syntax highlighting ready**: Styled for code display (though true syntax highlighting requires additional setup in Anki)
- **Dark theme**: Developer-friendly color scheme (Dracula-inspired)
- **Multi-language**: Works for any programming language

## Files

- `config.yaml` - "Code Snippet" note type optimized for code display
- `data.yaml` - Sample programming concepts from Python, JavaScript, Go, and SQL

## Building

```bash
anki-yaml-tool build --data data.yaml --config config.yaml --output programming.apkg --deck-name "Programming Concepts"
```

## Use Cases

Perfect for memorizing:
- Programming language syntax
- Design patterns
- Algorithm implementations
- Code idioms and best practices
- Standard library functions
- Framework-specific patterns
- SQL queries
- Shell commands

## Customization Ideas

### 1. Add Syntax Highlighting

For true syntax highlighting in Anki, you can:
- Use AnkiConnect with a syntax highlighter plugin
- Pre-format code with HTML `<span>` tags for colors
- Use Anki add-ons like "Syntax Highlighting for Code"

### 2. Add Output Field

Include expected output:

```yaml
- concept: "String Formatting"
  language: "python"
  code: |
    name = "Alice"
    print(f"Hello, {name}!")
  output: "Hello, Alice!"
  explanation: "F-strings (Python 3.6+) provide a clean way to embed expressions in strings."
```

### 3. Add Complexity Rating

Include time/space complexity for algorithms:

```yaml
- concept: "Binary Search"
  language: "python"
  code: |
    def binary_search(arr, target):
        left, right = 0, len(arr) - 1
        while left <= right:
            mid = (left + right) // 2
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        return -1
  complexity: "Time: O(log n), Space: O(1)"
```

### 4. Add References

Link to documentation or tutorials:

```yaml
- concept: "React Hooks"
  language: "javascript"
  code: |
    import { useState } from 'react';

    function Counter() {
      const [count, setCount] = useState(0);
      return <button onClick={() => setCount(count + 1)}>
        Count: {count}
      </button>;
    }
  reference: "https://react.dev/reference/react/hooks"
```

## Tips for Technical Cards

1. **Keep snippets small**: Focus on one concept per card
2. **Use realistic examples**: Prefer practical code over abstract examples
3. **Add context**: Include comments in code when helpful
4. **Tag strategically**: Use tags for language, difficulty, and topic
5. **Include edge cases**: Show common gotchas and pitfalls
6. **Link related concepts**: Use consistent IDs to cross-reference

## Tags Strategy

The example uses a three-tier tagging system:
- **Language**: `python`, `javascript`, `go`, `sql`
- **Category**: `basics`, `functions`, `syntax`, `best-practices`
- **Level**: `beginner`, `intermediate`, `advanced`

This allows creating focused study sessions by language, topic, or difficulty level.
