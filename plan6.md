# Plan 6 - Core2 execution constitution

## 1. Purpose

Ez a dokumentum a Core2 tényleges főterve.

Nem research dump.
Nem hosszú indoklás.
Nem narratíva.

Hanem az a kicsi, végrehajtható alkotmány, amiből ténylegesen kódolni lehet.

Alapja:

- `plan2.md`
- `plan3.md`
- `plan4.md`
- `plan5.md`
- `architect.md`
- a session közben rögzített tartós guardrailok

## 2. Product scope contract

Ez a Core2 valódi termékcélja.

Nem belső architektúra-esztétika.
Nem benchmark-pass önmagában.

Hanem ez:

1. `SOTA / bleeding-edge memory kernel`
- nem csak “helyes”
- hanem valós esélyű top-tier rendszer

2. `real-world first`
- nem benchmark-fogalmazásokra optimalizál
- benchmark csak megerősítés

3. `zero-devops, local-first`
- nincs külön ops-rendszer
- a truth store lokális, inspectálható, egyszerűen hordozható

4. `multilingual / locale-neutral`
- a core nem angol cue-listákon áll
- locale-specifikus cue csak adapterben élhet

5. `priority order`
- pontosság > token-spórolás > sebesség

6. `fast enough for real use`
- cél: kb. `5s` end-to-end
- kemény plafon: kb. `10s` end-to-end
- ez nem csak benchmarkra, hanem production-szerű használatra értendő

7. `large-memory viability`
- ne csak kis sessionöknél működjön
- legyen életszerű út `5k könyv`-szintű tudásállapotig

8. `anti-Frankenstein`
- az új rendszer legyen kisebb, tisztább, sűrűbb intelligenciájú
- ne sok régi repo összehegesztett uniója legyen

9. `anti-endless-patching`
- bounded batch-ek
- explicit redesign trigger
- explicit deletion/replacement accounting

10. `Hermes-fit without becoming a Hermes addon`
- a Core2 önálló memory-logika
- de a Hermes moduláris provider/runtime határához szabott

11. `tool-heavy session viability`
- a rendszer ne küldje vissza mindig a teljes tool surface-t
- közben mégis tudja, milyen toolok és artifactok állnak rendelkezésre
- a toolcalling réteg cache-barát maradjon

Rule:

- ha egy architekturális döntés nem segíti ezt a tíz pontot, nem Core2-döntés

## 3. Confidence model

A `plan6` nem kezelhet minden állítást ugyanúgy.

Három kötelező bizalmi szint van:

1. `hard law`
- ha sérül, a Core2-t nem szabad így megépíteni
- nem “jó ötlet”, hanem kötelező törvény

2. `strong hypothesis`
- erős architecturális fogadás
- elég erős ahhoz, hogy batch induljon rá
- de ha a proof ladderben elbukik, vissza kell venni vagy át kell tervezni

3. `open question`
- szándékosan nyitott
- nem csúszhat be csendben az implementációba
- csak explicit döntéssel mozdulhat el

Rule:

- `hard law` alapján építünk
- `strong hypothesis` alapján bounded módon kísérletezünk
- `open question` alapján nem kezdünk el kódolni

## 4. Hard laws

Ezek nem preferenciák.
Ezek Core2-kötelezettségek.

### 4.1. Truth laws

1. A `journal/raw trace` és a `canonical truth` két külön réteg.
2. A replay/history continuity, nem truth source.
3. A structured truth store a primary truth layer; az indexek és projectionök derived state-ek.
4. Correction / update first-class write esemény.
5. Provenance kötelező.
6. Validity kötelező.
7. Exact recallhoz verbatim evidenciához vissza kell tudni lépni.
8. A gist nem evidence.

### 4.2. Core laws

1. A core nyelvfüggetlen.
2. Locale-specifikus cue csak adapterben élhet.
3. Nem lehet második párhuzamos memory platform.
4. Nem lehet god object.
5. Nem lehet broad raw fallback a primary correctness pathban.
6. A delivery nem correctness engine.
7. A Hermes integráció vékony boundary legyen, nem mély fork.
8. A native memory csak bounded derived snapshot lehet, nem primary truth source.
9. A tool-surface stabil profile-okból álljon; turn-level schema churn nem lehet primary működési mód.

### 4.3. Product laws

1. Pontosság > token-spórolás > sebesség.
2. Ami új komponens nem vált ki régit, az gyanús.
3. Benchmark nem tervezési forrás, csak ellenőrzés.
4. A Core2-nek valós életben kell működnie, nem benchmark-fogalmazásokra.
5. Paid eval nem discovery eszköz, hanem megerősítő kapu.
6. Ha egy hiba nem fér bele az aktuális batch deklarált családjába, meg kell állni és a tervet kell javítani, nem a kódot foldozni.
7. Ha egy batch nem tud mérhetően egyszerűsíteni, nem tekinthető sikeresnek akkor sem, ha részlegesen javít.
8. Tool-heavy sessionökben a prompt cache stabilitása elsőrangú termékkövetelmény.

## 5. Explicit adopted invariants

Ezek a legerősebb, ténylegesen átvett invariánsok a külső rendszerekből.

### 5.1. From PLUR

1. Atomikus durable memory unit kell.
2. `episode/history` külön van a `knowledge/assertion` rétegtől.
3. Hit / miss / feedback loop kell.
4. Temporal validity kell.
5. Promotion quality gate kell: nem minden megfigyelésből lesz tartós memória.
6. Enriched hybrid retrieval jó irány:
   - lexical
   - semantic
   - structured cue

### 5.2. From CatRAG

1. Query-aware steering kell.
2. Bridge vs solution fegyelem kell.
3. A retrievalnek completeness-t is védenie kell, nem csak nearest-match-et.

### 5.3. From Mem0 / MemGPT / MemOS

1. Extract / consolidate / retrieve szétválasztása kell.
2. Working context és tartós memory külön réteg.
3. Local-first, zero-devops persistencia maradjon.
4. Drága memória-formálás ne a query-time kritikus ösvényen fusson.

### 5.4. From CogSci

1. Encoding / storage / retrieval külön folyamat.
2. Cue-first retrieval kell.
3. Source monitoring elsőrangú.
4. Working memory korlát valódi design constraint.
5. Interference kontroll kell:
   - dedupe
   - diversity
   - conflict markers
6. Abstention kötelező minőségi mechanizmus.

### 5.5. From Karpathy `llm-wiki`

1. `raw sources -> compiled layer -> schema`
2. Persistent compiled middle layer kell.
3. Index + log + lint/health-check szemlélet kell.

### 5.6. From prior Hermes planning

1. Stabil `tool_profile` kell, nem turnenként újraszórt tool schema.
2. A nagy tool output artifactként éljen, ne prompt payloadként.
3. A rendszer tudjon explicit rehydrate-olni artifactból, ne full replayből éljen.
4. A prompt cache stabilitása felülírja a turn-level tool gating ambíciót.

## 6. Current canonical Core2 proposal

Status:

- `strong hypothesis`

Ez az a minimális mag, amire érdemes Batch A-t indítani.
Nem hard law.
Ha nem igazolja a proof ladder, vissza kell venni.

### 6.1. Canonical objects

1. `entity`
2. `event`
3. `state`
4. `measure`
5. `source`

### 6.2. Canonical edges

1. `about`
2. `participant`
3. `object_of`
4. `located_at`
5. `has_state`
6. `has_measure`
7. `supported_by`
8. `quotes`
9. `supersedes`
10. `corrects`

### 6.3. Primary operators

1. `recall`
2. `attribute`
3. `count`
4. `aggregate`
5. `compare`
6. `temporal`

### 6.4. Typed answer contract

Minden operator outputja:

- `answer_type`
- `operator`
- `canonical_value`
- `display_value`
- `grounding_refs`
- `confidence_tier`
- `abstain_reason`

## 7. Why this could plausibly be SOTA

Status:

- `strong hypothesis`, not theorem

Ez a terv nem azért érdemes, mert “szebb”, hanem mert egyszerre több erős előnyt sűrít kisebb magba:

1. `accuracy`
- explicit truth contract
- provenance + correction + validity first-class
- typed answer object a snippet-húzás helyett

2. `multilingual robustness`
- locale-neutral core
- nyelvi cue csak adapterben
- nem angol-specifikus raw string logikán áll

3. `token efficiency`
- a kernel kész, typed választ ad át
- nem kell széles evidence-blobbal etetni a deliveryt minden esetben

4. `latency`
- a drága szemantikai munka write-timeba tolható
- query-time kis operator-készlet dolgozik kanonikus objektumokon

5. `maintainability`
- kevesebb primary mechanizmus
- kevesebb overlapping surface
- több replacement power, kevesebb fallback-mesh

6. `tool-heavy efficiency`
- a stabil tool profile és artifact-first rehydration erős prompt-cache és token-előnyt ad
- a rendszer nem full tool-schema újraküldéssel próbál continuityt tartani

Ez a SOTA-fogadás akkor falszifikálódik, ha:

1. a Core2 csak újabb réteget tesz a meglévő rendszerre, és nem vált ki primary útvonalakat
2. a Core2 accuracyt csak broad fallbackkel vagy benchmark-specifikus toldással tud tartani
3. a Core2 nem marad kisebb és tisztább a mostani primary correctness pathnál
4. a typed object/operator út nem tudja lefedni a valós kérdések döntő többségét family-specifikus escape hatch nélkül

## 8. Hard boundaries

### 8.1. Write-time

Write-time feladata:

- capture raw trace
- compile canonical objects
- build edges
- attach provenance
- attach correction/supersession
- persist truth

### 8.2. Query-time

Query-time feladata:

- parse canonical query contract
- operator select
- retrieve candidate objects
- execute operator
- emit typed answer object

### 8.3. Delivery-time

Delivery feladata:

- `final_compact`
- `supported_compact`
- `exploratory_full`
- `artifact_rehydrate`

Tiltott:

- a delivery újraírja a kernel válaszát
- a delivery találja ki a truthot
- a delivery nyers nagy tool outputot tol vissza promptba alapértelmezetten

## 9. Anti-loop execution protocol

Ez a szakasz azért van, hogy a Core2 ne újabb végtelen foldozás legyen.

### 9.1. Batch discipline

Minden batch előtt kötelező:

1. pontos scope
2. explicit `keep / cut / rebuild` cél
3. explicit modules-to-replace lista
4. explicit non-goals
5. explicit proof obligations
6. explicit replacement ledger
7. explicit deletion/demotion ledger

### 9.2. No exploratory coding

Tilos:

1. azért kódolni, hogy “majd a paid eval megmondja mi a következő hiba”
2. open questionre kódolni
3. sample-fixet vagy judge-shape fixet primary megoldásként bevinni
4. olyan új réteget hozzáadni, amelynek nincs azonnali replacement célja
5. turn-level tool schema churnt bevezetni cache-barát tool profile helyett

### 9.3. Paid eval rule

Paid eval csak akkor nyitható:

1. ha a batch lokális gate-jei zöldek
2. ha a deklarált replacement tényleg megtörtént
3. ha nincs új broad fallback a primary correctness pathban
4. ha a deletion/demotion ledger ténylegesen lezárt legalább egy régi primary útvonalat
5. ha a tool surface stabil profile-ból működik és nem igényel folyamatos schema-újraküldést

### 9.4. Correction-round cap

Egy batchre maximum:

1. `1` első implementációs kör
2. `2` korrekciós kör

Ha ezután még mindig új shared family bukik ki ugyanazon a batchen belül, nem újabb patch jön, hanem tervrevízió.

### 9.5. Redesign trigger

Azonnali stop és tervrevízió kell, ha:

1. a hiba nem fér bele az aktuális batch deklarált családjába
2. a fix nem vált ki régit, csak új réteget rak mellé
3. a fix locale-specifikus cue-ra vagy benchmark-shape-re épülne
4. a fix a deliveryt használná új correctness-engineként
5. a batch végén nincs valós complexity shrink vagy nincs lezárt replacement
6. a fix prompt-cache stabilitást rontó tool schema churnt vezetne be

### 9.6. Replacement/deletion accounting

Minden batch végén kötelező kimondani:

1. mi lett az új primary út
2. mely régi primary út szűnt meg vagy demotálódott
3. mely régi modul marad csak debug / compatibility / explicit fallback szerepben
4. milyen párhuzamos mechanizmust sikerült ténylegesen megszüntetni

Ha ez nincs, a batch nem tekinthető befejezettnek.

## 10. Proof ladder

Core2-t nem “érzésre” vezetjük be. Öt bizonyítási szint van.

### 10.1. Architecture proof

Bizonyítani kell, hogy:

1. a batch hard law-kompatibilis
2. a batch primary pathot egyszerűsít
3. a batch replacement powerrel bír

### 10.2. Local proof

Bizonyítani kell, hogy:

1. a typed answer object létrejön
2. a régi primary path demotálódik
3. a lokális és szintetikus suite-ok zöldek
4. a tool-heavy flow nem nő újra full-schema/full-output promptolás felé

### 10.3. Scalability proof

Bizonyítani kell, hogy:

1. a batch nem csak toy memory-állapoton működik
2. van production-szerű large-memory gate
3. a Core2-nek van hiteles út `5k könyv`-szintű tudásállapot felé
4. a kernel-local rész nem válik domináns késleltetési forrássá nagy állapotnál sem
5. a tool-heavy flowknál az artifact-first rehydration és a stabil tool profile megmarad

### 10.4. Live proof

Bizonyítani kell, hogy:

1. a paid eval csak megerősít, nem fedez fel új tervezési hiányt
2. nincs shared regresszió a batch deklarált scope-ján belül

### 10.5. Product proof

Bizonyítani kell, hogy:

1. a correctness nem romlik
2. a token-hatékonyság nem esik szét
3. a latency nem kényszerít vissza broad fallbackre vagy delivery-blobokra
4. a production-szerű end-to-end használatnak hiteles útja van a `~5s` cél és `~10s` plafon felé
5. a tool schema cost és a prompt-cache romlás nem nő vissza a régi szintre

## 11. Batch A

Ez az első tényleges megvalósítási kör.

### 11.1. Scope

1. shared object envelope
2. 5 canonical object
3. canonical edges
4. `attribute`
5. `count`
6. `aggregate`
7. typed answer contract
8. slim delivery
9. stable tool-profile boundary

### 11.2. Target module families

Új primary modulok:

- `core2_objects.py`
- `core2_edges.py`
- `core2_compiler.py`
- `core2_selector.py`
- `core2_operator_attribute.py`
- `core2_operator_count.py`
- `core2_operator_aggregate.py`
- `core2_answer.py`
- `core2_delivery.py`

### 11.3. Batch A non-goals

1. teljes replay-újratervezés
2. autoresearch loop
3. `compare` / `temporal` Batch B előtti beemelése
4. új benchmark-specifikus special-case családok felvétele
5. turn-level tool schema orchestration újrafelfújása

### 11.4. Batch A proof obligations

1. az `attribute / count / aggregate` primary út már nem a mai broad executor
2. a typed answer contract az elsődleges handoff
3. a delivery nem írja újra a kernel truthot
4. legalább egy jelentős régi primary compiled surface vagy executor-path ténylegesen demotálódik
5. a replacement ledger és a deletion ledger konkrétan lezárható
6. a tool-heavy prompt surface stabilabb vagy legalább nem rosszabb marad

## 12. Immediate cuts and demotions

Ezek nem maradhatnak primary correctness pathban a Core2 mellett.

1. generic raw-record fallback
2. broad general synthesis
3. overlapping compiled surface-háló
4. delivery mint answer-rewriter
5. query-time újrabányászás ott, ahol write-time object lehet
6. full tool schema újraküldés mint default continuity-mechanizmus

Maradhatnak:

- debug
- compatibility
- explicit fallback

De nem lehetnek primaryek.

## 13. Open hypotheses

Ezeket használjuk, de még nem kezeljük végleges törvényként.

1. Az 5 object pontosan elég-e hosszú távon.
2. A 6 operator pontosan elég-e hosszú távon.
3. A `dual-route retrieval` kell-e, és ha igen, milyen minimális formában.
4. Milyen mély legyen a bitemporal modell első körben.
5. Mennyire kell explicit `current-state snapshot` surface.

## 14. SOTA proof standard

Nem lehet azért SOTA-t mondani, mert a terv elegáns vagy egy benchmark jól sikerül.

Core2 csak akkor nevezhető SOTA-közelinek vagy SOTA-nak, ha:

1. a saját hard law-jait tartja
2. a primary path ténylegesen kisebb és tisztább lett
3. a replacement/deletion accounting alapján valódi régi primary rétegeket kiváltott
4. a correctness production-szerű használatban erős maradt
5. a token-hatékonyság nem trade-elődött el a pontosság rovására
6. a sebességnek hiteles, nagy állapotra is vállalható útja van
7. a multilingual viselkedés nem cue-listás heurisztikákon áll
8. a benchmark-eredmény csak megerősíti azt, ami belsőleg már bizonyított

## 15. Kill criteria

Ha ezek közül bármelyik teljesül, meg kell állni és újrabírálni a Core2-t.

1. Az új mag nem csökkenti a primary correctness path bonyolultságát.
2. Az új komponensek nem váltanak ki régit.
3. Újra fallback-háló kezd nőni.
4. Újra benchmark-familyk szerint kezdünk javítani object/operator helyett.
5. A delivery megint correctness-engineként viselkedik.
6. A batch-protokollt megkerüljük, és a paid eval újra discovery eszközzé válik.
7. A large-memory / latency irány nem javul, csak el van tolva későbbre.

## 16. Operating rule

Innentől a Core2 csak akkor tekinthető helyes iránynak, ha:

- kisebb
- tisztább
- általánosabb
- jobban illeszkedik a valódi product scope-hoz
- és bizonyíthatóan több régi primary réteget vált ki, mint amennyit hozzáad
