# plan8.md

## Cél

Ez a fájl **context-condensing álló handoff** a Hermes Core2 memória-kernel aktuális állapotáról.

Nem rövid státusz, hanem a fontos döntések, fázisok, anti-patternök, nyitott kérdések és a következő logikus irányok összefoglalója.

Ha a kontextus rövidül, **ebből kell visszaépíteni a munkát**.

---

## 1. Rövid igazságállítás

Jelenlegi legfontosabb állítások:

- A **Core2 deterministic truth kernelje** jelentősen előrehaladt, és több kör benchmark-loop után most már **nem a kernel látszik fő problémának**, hanem a külső gate/handoff réteg.
- A `04.7` fázis **saját célja szerint kész**.
- A projekt **még nincs teljesen kész**, mert a `04.1` végső fizetős 10-es gate rerunja még nyitva van.
- A jelenlegi legjobb hosszabb távú stratégia **nem** a MemPalace-re teljes váltás, hanem egy **rétegzett Core2 + MemPalace hibrid**, ahol:
  - MemPalace-szerű réteg adja a **lossless raw substrate + retrieval stack**-et
  - Core2 adja a **deterministic fact/truth kernel + abstention + answer surface** réteget

---

## 2. Nem alkuképes szabályok

Ezeket a munka során többször kimondtuk. Ezeket **nem szabad elfelejteni**:

1. **Ne mossuk össze a kernel-correctnesset az external judge / benchmark zajjal.**
2. **A hálózati / távoli modellkésés nem elsődleges kernelhiba-szignál.**
   - A user explicit tartós szabálya: a kínai/távoli szerver miatti lassulás ne legyen fő kernel-eval.
3. **Ne legyen végtelen family-expanzió.**
   - Nem topic-specifikus familyket építünk (`coins`, `records`, `cameras` stb.), hanem **általános memory patternöket**.
4. **Ne legyen benchmark-smink a kernel magjában.**
   - Nem kerülhet benchmark-specifikus angol phrasing vagy hardcode truth logic a deterministic core-ba.
5. **A deterministic core boundary maradjon tiszta.**
6. **A comparator maradjon szűk és fail-closed.**
   - Nincs “close enough” semantic matching.
7. **Egy rétegnek egy gazdája legyen.**
   - Nem építünk két párhuzamos “okos memória” rendszert egymás tetejére.
8. **A 04.6 handmade acceptance és gate matrix nem dísz, hanem workflow-szabály.**

---

## 3. Hol tart most a projekt?

### Fő nyitott phase

- **Nyitott phase**: `04.1`
- Teljes neve: `Kernel Correctness And Live Gate Recovery`
- Állapot:
  - a korábbi ködös live-gate problémát több beszúrt phase tisztázta
  - most már a `04.1` tényleg a **végső fizetős 10-es gate rerun** fázisa

### Kész inserted phase-ek

- `04.2` — Write-Time Fact Digestion
- `04.3` — Fact-First Recall
- `04.4` — Uncovered Durable Memory Families
- `04.5` — Deterministic Answer Surface And Gate Closure
- `04.6` — Core Axioms And Handmade Acceptance
- `04.7` — Authoritative Gate Compatibility

### Miért volt erre szükség?

Mert a `04.1` eredeti formájában túl ködös lett volna:

- benchmark-loop
- heurisztikus foltozás veszélye
- kernelhiba vs judge artifact összemosása
- finish line bizonytalanság

Az inserted phase-ek ezt szedték szét.

---

## 4. Phase-enként a valódi eredmény

### 04.2 — Write-Time Fact Digestion

Mit adott:

- bounded write-time fact extraction
- current/previous fact canonicalization
- `derived_from` provenance edge
- `fact_key` retrieval index
- `fact_compact` delivery view

Ez volt az első komoly lépés a query-time blob-értelmezés visszaszorítására.

### 04.3 — Fact-First Recall

Mit adott:

- a recall covered queryknél tényleg a digesztált fact-réteget preferálja
- csak utána esik vissza szélesebb keresésre

Ez már valós architekturális javítás volt.

### 04.4 — Uncovered Durable Memory Families

Mit adott:

- preference / habit / routine
- aggregate / count
- bounded temporal summary / event anchors

Plusz:

- family coverage contract
- structured-only fast-path guard
- machine-readable gate status

### 04.5 — Deterministic Answer Surface

Mit adott:

- provider-owned answer surface
- külön serializer/handoff réteg
- nem loose recall blob megy tovább

Ez volt a helyes irány a handoff rendbetételéhez.

### 04.6 — Core Axioms And Handmade Acceptance

Mit adott:

- explicit hard deterministic core boundary
- kicsi handmade acceptance benchmark
- golden paths
- gate matrix

Ez egy **steering/control phase** volt, nem közvetlen kód-javító phase.

Fontos: a `04.6` **nem váltotta ki** a `04.1`-et, hanem **megalapozta és újraértelmezte**.

### 04.7 — Authoritative Gate Compatibility

Mit adott:

- strict local comparator a promptless authoritative válaszokra
- fail-closed gate classification
- canary-first proof
- explicit handback `04.1`-re

Eredmény:

- local proof zöld
- 5-ös external canary: **5/5 passed**
- `api_calls: 0` mind az 5 esetben
- `answer_surface_hit_rate: 1.0`

Ezért a `04.7` **saját célja szerint kész**.

---

## 5. A 04.6 kemény magja

Ez a projekt jelenlegi legfontosabb architekturális szabályrendszere.

### Deterministic hard core

1. Stable fact identity
2. Provenance
3. Temporal state
   - current / previous / superseded
4. Conflict is first-class
5. Deterministic supersession
6. Fact-first recall for covered families
7. Fail-closed answer surface
8. Abstention

### Explicitly outside the hard core

Ezek **nem** claimed deterministic guarantees:

- raw text -> fact candidate extraction
- broad semantic matching
- relation/graph proposal
- summarization
- fuzzy ranking for weak matches
- final stylistic phrasing
- external benchmark judge behavior

Ez a határ kritikus.

---

## 6. A 04.7 lényege és pontos korlátai

### Mit csinál a 04.7 comparator?

Nem általános judge-helyettesítő.

Hanem:

- csak **promptless authoritative** esetekben fut
- csak **covered structured kinds** esetén fut
- ha nincs szűk mechanikus összehasonlíthatóság, akkor `not_applicable`

Támogatott structured kindok:

- `aggregate_count`
- `temporal_elapsed`
- `trip_order`
- `preference_guidance`
- `scalar`

### Mit NEM szabad csinálni vele?

- nem lehet soft semantic “kábé jó” matcher
- nem lehet benchmark-overfitelt if-else temető
- nem lehet kernel-truth engine

### Miért kellett?

Mert a promptless authoritative short-circuit (`api_calls: 0`) út a külső judge-ban korábban túl sok:

- `unknown`
- `prompt_miss`
- hamis handoff zaj

eredményt generált.

### A 04.7 legfontosabb óvatossági szabálya

A comparator **csak gate compatibility layer**, nem a truth engine része.

---

## 7. A másik agentek kritikáiból mi lett elfogadva?

### Amit elfogadtunk

1. A temporary benchmark-közeli angol phrasing a core-ban rossz irány volt.
   - kiszedtük / visszavontuk
2. A külön serializer/handoff réteg helyes.
   - `core2_answer_surface.py`
3. A `hosszabb = jobb` trip-dedupe heurisztika gyenge volt.
   - javítva
4. A comparator nem lehet túl megengedő.
   - szűk/fail-closed maradt
5. A canary zöld önmagában nem elég.
   - csak explicit blocker-rendezés után jöhet paid rerun

### Amit csak részben fogadtunk el

1. A regex-sprawl kritika
   - **részben igaz**
   - a digestion extractorok tényleg hordoznak törékenységi kockázatot
   - de ebből **nem** következik automatikusan, hogy most LLM-only structured extractionre kell váltani
   - ez jelenleg inkább **bounded technical debt**, nem irányváltási trigger

### Amit túlzónak tekintettünk

1. Minden richer handoff phrasing benchmark-smink
   - nem, ha a plusz phrasing valódi constraintet / szemantikai fidelity-t őriz meg

---

## 8. Aktuális 04.1 / gate igazság

### Mi van kész?

- a `04.7` után a promptless authoritative compatibility rés **rendezett**
- a 5-ös canary **zöld**
- a fizetős `10`-es rerun **zöld** lett
- a `04.1` sampled baseline ezért formálisan lezárható volt

### Mi nincs kész?

- a szélesebb stabilitás **nincs még bizonyítva**
- a későbbi fizetős `20`-as confirmation run megmutatta, hogy a sampled `10/10` még nem általánosult elég szélesen

### Nagyon fontos

A `10/10` sampled lezárás **nem hamis**, de a `20/20` után már azt látjuk, hogy a jelenlegi Core2-ben maradt egy új, tisztább gap:

- **nem** a promptless-authoritative ág omlik össze
- **nem** végtelen új familyk hiányoznak
- hanem kb. `3` általános pattern még nincs eléggé surface-re emelve:
  1. generic aggregate totals / thresholds
  2. generic event ordering / temporal compare
  3. canonical abstention surface

Ezért a következő jó lépés **nem** rögtön a MemPalace-codemap, hanem előbb egy általánosító Core2 phase.

---

## 9. MemPalace értékelés — a jelenlegi álláspont

### MemPalace miben erős?

Erős rétegek:

- lossless raw storage
- verbatim drawers / closets
- semantic search
- wing / room scoped retrieval
- optional rerank
- AAAK / wake-up compression
- egyszerű helyi temporal KG

### MemPalace miben nem bizonyított jobb teljes replacement?

Nem ugyanazt a problémát oldja teljesen, mint a Core2.

Fő gond:

- a README/benchmark claimjei főleg **retrieval recall** körül forognak
- nem ugyanaz az end-to-end deterministic truth kernel, mint amit mi építünk

LongMemEval claimje:

- `R@5`
- retrieval-heavy story

Ez nagyon fontos, mert:

- retrievalben lehet jobb
- full deterministic truth-state answer kernelként még nem bizonyított kész replacement

### Jelenlegi verdict

- **Substrate/retrieval layerben**: `MemPalace > current Core2`
- **Truth/state/answer discipline-ben**: `Core2 > MemPalace`
- **Final targetként**: `Core2 + MemPalace` a legígéretesebb

### Mit nem szabad tenni?

- nem szabad wholesale repo-váltani most
- nem szabad két párhuzamos truth engine-t építeni

---

## 10. A réteges jövőkép

Ez most a legfontosabb hosszabb távú döntés.

### L0 — raw corpus / lossless store

Legjobb irány:

- **MemPalace-szerű**

### L1 — retrieval / scope / optional rerank

Legjobb irány:

- **MemPalace-szerű**

### L2 — deterministic truth kernel

Legjobb irány:

- **Core2**

Mit tartson ez meg:

- fact identity
- provenance
- current/previous/superseded
- conflict/supersession
- abstention

### L3 — deterministic answer surface / gate discipline

Legjobb irány:

- **Core2**

### Következtetés

A jó architektúra **nem**:

- `Core2 -> MemPalace` váltás

Hanem:

- `MemPalace substrate + Core2 truth kernel + Core2 answer surface`

Ez a harmonikus mix.

---

## 11. Javasolt következő GSD sorrend

### Azonnal

1. `NE` ugorjunk még rögtön a MemPalace-adoption fázisra

Miért:

- a `10/10` adott egy sampled baseline-t
- de a `20/20` már kimondottan azt mutatja, hogy van még egy **általánosító surface-gap** a Core2-ben
- ezt jobb előbb leválasztani és külön lezárni, különben a MemPalace-vonalat összekeverjük a jelenlegi Core2 hiányosságaival

### Utána

#### 04.8

Név:

- `Generic Surface Generalization`

Cél:

- a `20/20` bukó minták mögött álló **általános pattern gapet** zárjuk le
- célzottan:
  - generic aggregate totals / thresholds
  - generic event ordering / temporal compare
  - canonical abstention surfaces

Kimenetek:

- egy tiszta Core2 phase, ami után már nem a fallback/handoff surface-hiány fogja torzítani a későbbi MemPalace döntést
- új local proof + rerun evidence a generikus surface-ekre

#### 04.9

Név:

- `MemPalace Codemap And Adoption Matrix`

Cél:

- pontosan bontsuk szét:
  - `adopt as-is`
  - `adapt into Core2`
  - `reject / keep Core2`

Ownership:

- `elemzés`

#### 04.10

Név:

- `Shadow Retrieval Substrate`

Cél:

- MemPalace-szerű lossless retrieval substrate shadow módban
- még nem truth engine

Ownership:

- `MemPalace > Core2`

#### 04.11

Név:

- `Core2 Truth On MemPalace Substrate`

Cél:

- a deterministic truth kernel maradjon Core2
- de a raw/fallback retrieval substrate már az új rétegből jöjjön

Ownership:

- `Core2 + MemPalace`

#### 04.12

Név:

- `Optional Rerank Layer`

Cél:

- csak fallback / hard query eseteknél
- ne legyen always-on

Ownership:

- `Core2 + MemPalace`

#### 04.13

Név:

- `Graph And Navigation Decision`

Cél:

- csak akkor, ha tényleg ad pluszt
- nem lehet két truth engine

Ownership:

- opcionális `Core2 + MemPalace`

#### 04.14

Név:

- `Final Hybrid Comparison Gate`

Cél:

- hasonlítsuk össze:
  - current Core2
  - MemPalace substrate
  - hibrid

És csak utána legyen végső architektúra-döntés.

---

## 12. Mit NEM szabad elfelejteni a MemPalace-irányban?

1. Nem a README marketingjét integráljuk, hanem a valóban hasznos réteget.
2. Nem építünk két KG-t egyszerre.
3. Nem cseréljük le a Core2 truth-state rétegét olyan elemre, ami csak retrievalben erős.
4. Nem vállaljuk be automatikusan a manual KG protocolt.
5. A retrieval-substrate lehet MemPalace, de a **truth owner** maradjon egyetlen rendszer.

---

## 13. Mi marad szándékosan nyitott?

Ez a fájl **nem** azt jelenti, hogy minden el van döntve örökre.

Az alábbi pontok **tudatosan újragondolhatók**, ha új evidence jön:

1. **MemPalace átvételi aránya**
   - A jelenlegi álláspont: retrieval/substrate-ben erős.
   - Ez később nőhet vagy csökkenhet a shadow benchmark után.
   - A `20/20` evidence miatt előbb a Core2 generikus surface-gapet kell leválasztani róla.

2. **A graph/KG szerepe**
   - Jelenleg secondary vagy későbbi rétegként kezeljük.
   - Ha a shadow/hybrid mérések szerint valódi pluszt ad, előrébb jöhet.

3. **Regex-alapú write-time extraction sorsa**
   - Jelenleg bounded technikai adósságként kezeljük.
   - Ha törékenységi evidence jön, át lehet térni jobb structured extraction irányra.

4. **Comparator hosszabb távú sorsa**
   - Jelenleg 04.7 kompatibilitási réteg.
   - Nem szabad végleges truth-engine-né merevíteni.

5. **Rerank szükségessége**
   - Most optional fallback layerként gondolunk rá.
   - Ha a hibrid substrate önmagában elég, nem kell mindig bekötni.

6. **A final target pontos formája**
   - Jelenlegi legjobb hipotézis: `MemPalace substrate + Core2 kernel`.
   - Ez csak akkor marad végleges, ha a későbbi mérés is ezt igazolja.

### Mit NEM szabad újragondolhatóként kezelni?

Ezeket továbbra is stabil alapnak tekintjük:

- egy rétegnek egy gazdája legyen
- ne legyen két párhuzamos truth engine
- kernelhiba != benchmark/judge zaj
- nincs benchmark-smink a deterministic core-ban
- a 04.6 hard core boundary maradjon explicit

Ez a szakasz azért van itt, hogy a fájl **ne legyen túl merev**, de a fontos védőkorlátok se vesszenek el.

---

## 14. Fontos fájlok, amiket resume-kor nézni kell

### Core2 references

- `.planning/references/CORE2-AXIOMS.md`
- `.planning/references/CORE2-HANDMADE-BENCH.md`
- `.planning/references/CORE2-GOLDEN-PATHS.md`
- `.planning/references/CORE2-GATE-MATRIX.md`

### 04.1 current gate

- `.planning/phases/04.1-longmemeval-gate-and-performance-fixes/04.1-GATE-STATUS.json`
- `.planning/phases/04.1-longmemeval-gate-and-performance-fixes/04.1-VERIFICATION.md`

### 04.7 proof

- `.planning/phases/04.7-authoritative-gate-compatibility/04.7-01-SUMMARY.md`
- `.planning/phases/04.7-authoritative-gate-compatibility/04.7-02-SUMMARY.md`
- `.planning/phases/04.7-authoritative-gate-compatibility/04.7-03-SUMMARY.md`
- `.planning/phases/04.7-authoritative-gate-compatibility/04.7-VERIFICATION.md`

### Current key code

- `agent/core2_runtime.py`
- `agent/core2_digestion.py`
- `agent/core2_fact_registry.py`
- `agent/core2_authoritative.py`
- `agent/core2_answer_surface.py`
- `agent/core2_longmemeval_benchmark.py`

### MemPalace local checkout used in analysis

- `/tmp/mempalace`

---

## 15. A legfontosabb “ne csússzunk vissza” mondatok

Ha csak 10 dolgot lehet megtartani ebből a fájlból, ezek legyenek:

1. `04.7` kész, de a projekt még nem kész.
2. Következő lépés: `/gsd-execute-phase 04.1`
3. A hálózati/model latency nem elsődleges kernelhiba-szignál.
4. Nincs több végtelen family-expanzió.
5. Nincs benchmark-smink a deterministic core-ban.
6. A comparator szűk, fail-closed gate layer marad.
7. MemPalace retrieval/substrate-ben erős.
8. Core2 truth-state/answer discipline-ben erős.
9. A jó jövőkép: `MemPalace substrate + Core2 kernel`, nem wholesale váltás.
10. Egy rétegnek egy gazdája legyen.

---

## 16. Aktuális rövid végállapot

**Mostani igaz állapot:**

- `04.7`: kész
- `04.1`: nyitott
- `04.1` következő értelmes mozdulata: **fizetős 10-es rerun**
- MemPalace: **nem replacement**, hanem **nagyon erős substrate-jelölt**

Ez a jelenlegi legpontosabb összkép.
