# Split planner — multi-topic file → spec + references decomposition

Ты планируешь, как разбить cleaned single-file на структурированный набор `spec-*.md` + `references-*.md` файлов. Это Phase 10 в cleanup pipeline, опциональная — запускается только если файл содержит несколько чётко отдельных topic'ов.

## Входные данные

- **Cleaned файл:** `{cleaned_path}` — после Phase 8 final verification, single output
- **Total lines:** `{total_lines}`
- **Sections:** `{section_list}` — список `## ` headers из файла

## Когда split НЕ имеет смысла

- Файл <100 строк → один topic, splitting overhead не оправдан.
- Все секции тематически связаны (один проект, одна фича) → ничего не выигрываем.
- Секции делятся по типу контента, но не по теме (например, все про authentication: tasks, references, decisions) → лучше оставить одним файлом.

Если split не нужен → output `NO_SPLIT_NEEDED` с одной строкой причины.

## Что делать (когда split имеет смысл)

1. **Идентифицируй темы.** Группируй секции по логическим topic'ам (название проекта, область кода, отдельная фича).
2. **Для каждой темы определи:**
   - `spec-<slug>.md` — основной контент (tasks, goals, requirements, decisions, AC)
   - `references-<slug>.md` — links, research, raw data, external refs, цитаты
3. **Cross-references** — какой spec ссылается на какой references-файл.
4. **Line counts** — estimated lines per output file (по строкам секций, которые туда переедут).

## Output формат

```markdown
# Split Plan: <filename>

## Output files

### spec-<topic-A-slug>.md (~<N> lines)
Sections: `## Header 1`, `## Header 2`, ...
Content: <одна фраза описания>

### references-<topic-A-slug>.md (~<M> lines)
Sections: `## Header 3`, `## Header 4`, ...
Content: <одна фраза, обычно "links and external refs for topic A">

### spec-<topic-B-slug>.md (~<K> lines)
Sections: ...
Content: ...

### references-<topic-B-slug>.md (~<L> lines)
Sections: ...
Content: ...

## Cross-references
- spec-<A>.md → references-<A>.md
- spec-<B>.md → references-<B>.md
- (если темы пересекаются: spec-<A>.md → references-<B>.md тоже)

## Coverage check
Total source lines: <total>
Sum of output lines: <sum>
Headers added (TOC, cross-ref): ~<delta>
Expected: sum ≈ total + delta (every source line lands in exactly one output file)
```

## Антипаттерны

❌ Дробить one topic на много мелких файлов — split нужен, когда есть РЕАЛЬНО разные темы.  
❌ Делать `spec-foo.md` без `references-foo.md` (или наоборот), если в исходнике есть обе категории контента для темы.  
❌ Оставлять source-секции без destination — каждая `## ` секция должна попасть ровно в один output-файл.  
❌ Игнорировать line budgets — если `spec-A.md` получается 500+ строк, это плохая декомпозиция.

## Авторитет

Этот этап существует, потому что cleanup-файлы часто становятся слишком большими/смешанными для одного `/clarify` cycle. Если разбиение не помогает фокусу downstream-скиллов — оно бессмысленно. Не дроби ради дробления.
