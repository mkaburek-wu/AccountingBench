# Praxisfall KPMG — IFRS 10 Beherrschungsanalyse

**Entwurf der Benchmark-Aufgaben zur fachlichen Bestätigung**

Paul Schwarz GmbH & Co. KG · AccountingBench, WU Wien · Stand: Entwurf, noch nicht freigegeben

---

## Worum wir bitten

Dieser Entwurf setzt den von Ihnen übermittelten Praxisfall in acht
Benchmark-Aufgaben um. Die Modelle erhalten ausschließlich den Gesellschaftsvertrag
und die Anlagen 1 bis 3 — nicht Ihre E-Mail und nicht Ihren KI-Dialog, damit die
Ersteinschätzung wie von Ihnen gewünscht ohne fachliche Hilfestellung erfolgt.

Die Aufgaben 1 bis 6 zerlegen den Fall in einzelne Prüfungsschritte. Aufgabe 7
verlangt eine zusammenhängende fachliche Stellungnahme, also das Arbeitsergebnis,
das Sie selbst erstellen würden. Aufgabe 8 stellt dieselben sechs Einzelfragen noch
einmal, aber gebündelt in einem Durchgang. Der Vergleich zwischen den Einzelaufgaben
und Aufgabe 8 zeigt uns, ob die Modelle schwächer werden, wenn sie alle Schritte
gleichzeitig bearbeiten müssen — praktisch die Frage, ob eine schrittweise Führung
durch den Fall der entscheidende Faktor ist.

Die **Musterlösungen** (`gold_answer`) beruhen auf Ihrer abschließenden
Beurteilung; die jeweils angeführte Klauselkette ist unsere Herleitung dazu.
Die **Bewertungskriterien** (`grading_criteria`) steuern den LLM-Judge, der die
Modellantworten auf einer Skala von 0 bis 100 bewertet.

Wir bitten um Rückmeldung insbesondere zu:

1. Ist die Klauselkette in jeder Musterlösung fachlich zutreffend?
2. **Aufgabe 6 und Ziffer 7 von Aufgabe 7** — die Konsequenz nach IAS 28
   (maßgeblicher Einfluss, Equity-Methode) ist unsere Herleitung und in Ihrer
   Stellungnahme nicht ausdrücklich enthalten. Teilen Sie diese Einschätzung?
3. Sind die in `acceptable_variants` zugelassenen Abweichungen aus Ihrer Sicht
   vertretbar, oder fehlen weitere vertretbare Lösungswege?
4. Sind die Punkteabzüge in den Bewertungskriterien angemessen gewichtet?

Erst nach Ihrer Bestätigung werden die Aufgaben eingespielt und die Modelle
ausgeführt.

## Dokumente, die den Modellen vorgelegt werden

| # | Dokument | Inhalt |
|---|---|---|
| 1–4 | `GV_Teil1_Par1-7`, `GV_Teil2_Par8-11`, `GV_Teil3_Par12-18`, `GV_Teil4_Par19-20` | Gesellschaftsvertrag, Paragraphen 1 bis 20 |
| 5–6 | `Anlage1_Genehmigungscheckliste_Teil1`, `_Teil2` | Anlage 1 — Genehmigungscheckliste Projektverträge |
| 7 | `Anlage2_Freigaberegelung` | Anlage 2 — Freigaberegelung |
| 8 | `Anlage3_Geschaeftsordnung` | Anlage 3 — Geschäftsordnung für Geschäftsführer und Prokuristen |

Die Aufteilung ist rein technisch bedingt: unsere Pipeline kürzt Einzeldokumente ab
12.000 Zeichen, weshalb beide Quellen entlang ihrer eigenen Gliederung aufgeteilt
wurden. Inhaltlich ist nichts entfallen; kein Paragraph ist getrennt worden.

---


## Aufgabe 1 — `20260924_0001`

**Antworttyp:** open_text

### Fragestellung

Sie sind Wirtschaftsprüfer/in und beurteilen für Zwecke des IFRS-Konzernabschlusses der Max Huber Rail Group, wer die Paul Schwarz GmbH & Co. KG (Sitz Augsburg, Gleisbauunternehmen) beherrscht.

Grundlage sind ausschließlich die beigefügten Dokumente: der Gesellschaftsvertrag der Paul Schwarz GmbH & Co. KG (DOKUMENT 1 bis 4, Paragraphen 1 bis 20) sowie die Anlagen zu diesem Vertrag (DOKUMENT 5 und 6: Anlage 1 Genehmigungscheckliste Projektverträge; DOKUMENT 7: Anlage 2 Freigaberegelung; DOKUMENT 8: Anlage 3 Geschäftsordnung für die Geschäftsführer und Prokuristen).

Zitieren Sie die von Ihnen herangezogenen Bestimmungen jeweils mit Paragraph, Absatz und gegebenenfalls Ziffer.

FRAGESTELLUNG:
Welche Partei beherrscht die Paul Schwarz GmbH & Co. KG im Sinne von IFRS 10?

Antworten Sie in höchstens drei Sätzen. Nennen Sie entweder die beherrschende Partei oder stellen Sie fest, dass keine Partei beherrscht, und begründen Sie das Ergebnis knapp. Gehen Sie dabei ausdrücklich sowohl auf eine Alleinbeherrschung nach IFRS 10 als auch auf eine gemeinschaftliche Führung nach IFRS 11 ein.

### Musterlösung (gold_answer)

Keine Partei beherrscht die Paul Schwarz GmbH & Co. KG.

Eine Alleinbeherrschung nach IFRS 10 liegt nicht vor: Die Max Huber Rail GmbH verfügt zwar über besondere Entscheidungsrechte (Paragraph 6 Abs. 8 des Gesellschaftsvertrags), kann diese aber nur innerhalb des durch das Jahresbudget vorgegebenen Rahmens ausüben. Entscheidend ist daher, wer das Budget festlegen kann; die Festlegung des Jahresbudgets ist nach Anlage 3 Paragraph 3 Abs. 1 Nr. 3 ein zustimmungspflichtiges Geschäft und erfordert nach Paragraph 9 Abs. 2 Nr. 3 eine Mehrheit von 2/3 der Stimmen der anwesenden und vertretenen stimmberechtigten Kommanditisten. Mit 625.000 von 1.250.000 Stimmen (Paragraph 9 Abs. 4: je 1 EUR des Kapitalkontos eine Stimme) hält die Max Huber Rail GmbH genau 50 % und kann das Budget nicht einseitig bestimmen.

Auch eine gemeinschaftliche Führung nach IFRS 11 liegt nicht vor, weil für den Budgetbeschluss nicht die Zustimmung bestimmter, vertraglich festgelegter Parteien erforderlich ist, sondern unterschiedliche Gesellschafterkonstellationen die notwendige Mehrheit erreichen können.

### Zugelassene Abweichungen (acceptable_variants)

Zulässig sind Formulierungen wie 'niemand beherrscht', 'keiner der Gesellschafter beherrscht allein und es besteht auch keine gemeinschaftliche Führung' oder 'weder Beherrschung nach IFRS 10 noch joint control nach IFRS 11'. Die zusätzliche Feststellung, dass die Komplementärin AB Gleisbau GmbH trotz alleiniger Geschäftsführungsbefugnis nicht beherrscht, weil sie als Agent im Sinne von IFRS 10.B58 ff. handelt (keine Kapitaleinlage, kein Stimmrecht, keine Ergebnisbeteiligung), ist richtig und darf nicht als Fehler gewertet werden. Der Verweis auf 2/3 statt auf eine konkrete Prozentzahl ist gleichwertig.

### Bewertungskriterien (grading_criteria)

Answer must contain: (1) das Ergebnis, dass KEINE Partei die Paul Schwarz GmbH & Co. KG beherrscht. (2) die ausdrückliche Verneinung der Alleinbeherrschung nach IFRS 10. (3) die ausdrückliche Verneinung der gemeinschaftlichen Führung nach IFRS 11. (4) als Begründung zumindest im Ansatz, dass die besonderen Entscheidungsrechte der Max Huber Rail GmbH nur innerhalb des Budgetrahmens bestehen und die Max Huber Rail GmbH das Budget nicht einseitig festlegen kann.

Bewertung: Wird als Ergebnis die Max Huber Rail GmbH, die Familie Schwarz, die Komplementärin oder irgendeine andere Partei als beherrschend genannt, ist die Antwort im Ergebnis falsch: höchstens 10 Punkte, unabhängig von der Qualität der Begründung. Wird nur die Alleinbeherrschung verneint, die gemeinschaftliche Führung aber nicht angesprochen oder sogar bejaht, sind höchstens 50 Punkte zu vergeben. Volle Punktzahl nur, wenn (1) bis (3) erfüllt sind und (4) wenigstens sinngemäß enthalten ist. Eine korrekte Schlussfolgerung ohne jede tragfähige Begründung ist mit höchstens 65 Punkten zu bewerten. Der Umfang der Antwort ist kein Bewertungskriterium; eine knappe, vollständige Antwort ist voll zu werten.


---


## Aufgabe 2 — `20260924_0002`

**Antworttyp:** open_text

### Fragestellung

Sie sind Wirtschaftsprüfer/in und beurteilen für Zwecke des IFRS-Konzernabschlusses der Max Huber Rail Group, wer die Paul Schwarz GmbH & Co. KG (Sitz Augsburg, Gleisbauunternehmen) beherrscht.

Grundlage sind ausschließlich die beigefügten Dokumente: der Gesellschaftsvertrag der Paul Schwarz GmbH & Co. KG (DOKUMENT 1 bis 4, Paragraphen 1 bis 20) sowie die Anlagen zu diesem Vertrag (DOKUMENT 5 und 6: Anlage 1 Genehmigungscheckliste Projektverträge; DOKUMENT 7: Anlage 2 Freigaberegelung; DOKUMENT 8: Anlage 3 Geschäftsordnung für die Geschäftsführer und Prokuristen).

Zitieren Sie die von Ihnen herangezogenen Bestimmungen jeweils mit Paragraph, Absatz und gegebenenfalls Ziffer.

FRAGESTELLUNG:
Welches sind die maßgeblichen Tätigkeiten (relevant activities) der Paul Schwarz GmbH & Co. KG im Sinne von IFRS 10.10 ff., und welche dieser Tätigkeiten ist für die Beurteilung der Beherrschung letztlich ausschlaggebend?

Begründen Sie, warum gerade diese Tätigkeit den Ausschlag gibt.

### Musterlösung (gold_answer)

Maßgebliche Tätigkeiten sind die Tätigkeiten, die die Rendite der Gesellschaft wesentlich beeinflussen, also das operative Gleisbaugeschäft: insbesondere die Teilnahme an Ausschreibungen, die Beteiligung an Arbeitsgemeinschaften und das Eingehen von Subunternehmerverhältnissen sowie Investitionsentscheidungen (Paragraph 6 Abs. 8 des Gesellschaftsvertrags). Hinzu tritt als übergeordnete Steuerungsentscheidung die Festlegung des Jahresbudgets, das nach Anlage 3 Paragraph 3 Abs. 1 Nr. 3 den Umsatz-, Aufwand- und Ergebnisplan, den Personalplan, den Investitionsplan und den Finanzplan umfasst.

Ausschlaggebend ist die Festlegung des Jahresbudgets. Die operativen Entscheidungsrechte, die der Max Huber Rail GmbH zustehen, können nach dem Wortlaut des Paragraph 6 Abs. 8 nur innerhalb des bestehenden Budgets ausgeübt werden - Investitionsentscheidungen ausdrücklich nur 'innerhalb der bestehenden Budgetplanung'. Zusätzlich wird die Teilnahme an Ausschreibungen durch den nach Paragraph 6 Abs. 5 verbindlichen Genehmigungsprozess der Anlage 1 begrenzt, der weder der Disposition der Gesellschaft noch der Gesellschafter oder Geschäftsführer unterliegt und Projekte oberhalb bestimmter Schwellen der Genehmigung durch Marktverantwortlichen, CEO oder Oberste Leitung der Max Huber Rail Group unterwirft.

Wer das Budget bestimmt, setzt damit den Rahmen für sämtliche übrigen maßgeblichen Tätigkeiten. Die Beherrschungsfrage entscheidet sich daher daran, wer über die Festlegung des Jahresbudgets bestimmen kann, und nicht daran, wer die operativen Einzelentscheidungen innerhalb dieses Rahmens trifft.

### Zugelassene Abweichungen (acceptable_variants)

Eine weitergehende Aufzählung operativer maßgeblicher Tätigkeiten (Auftrags- und Projektakquise, Preis- und Kalkulationsentscheidungen, Personal- und Kapazitätssteuerung, Finanzierung) ist richtig, solange die Festlegung des Jahresbudgets als die ausschlaggebende Tätigkeit identifiziert wird. Statt 'Jahresbudget' sind 'Budgetfestlegung', 'Jahresplanung' oder 'Genehmigung der Unternehmensplanung' gleichwertig. Der zusätzliche Hinweis, dass die Festlegung des zustimmungspflichtigen Geschäftskatalogs selbst (Paragraph 6 Abs. 4) eine vorgelagerte Steuerungsebene bildet, ist zutreffend und nicht als Fehler zu werten.

### Bewertungskriterien (grading_criteria)

Answer must contain: (1) eine zutreffende Bestimmung der maßgeblichen Tätigkeiten als die renditewesentlichen operativen Tätigkeiten des Gleisbaugeschäfts (Ausschreibungen, ARGEn/Subunternehmerverhältnisse, Investitionen). (2) die Identifikation der Festlegung des Jahresbudgets als die ausschlaggebende maßgebliche Tätigkeit. (3) die Begründung, dass die operativen Entscheidungsrechte nach Paragraph 6 Abs. 8 nur innerhalb des Budgetrahmens ausgeübt werden können, mit Bezug auf die Formulierung 'innerhalb der bestehenden Budgetplanung'. (4) die Schlussfolgerung, dass die Beherrschungsfrage sich daran entscheidet, wer das Budget bestimmen kann.

Bewertung: Punkt (2) ist der Kern der Aufgabe. Eine Antwort, die maßgebliche Tätigkeiten nur allgemein beschreibt, das Budget aber nicht als ausschlaggebend erkennt, ist mit höchstens 35 Punkten zu bewerten, auch wenn sie im Uebrigen fachlich sauber ist. Werden (2) und (3) erfüllt, sind mindestens 70 Punkte zu vergeben. Der zusätzliche Verweis auf den verbindlichen Genehmigungsprozess der Anlage 1 (Paragraph 6 Abs. 5) ist verdienstvoll, aber nicht zwingend erforderlich.


---


## Aufgabe 3 — `20260924_0003`

**Antworttyp:** open_text

### Fragestellung

Sie sind Wirtschaftsprüfer/in und beurteilen für Zwecke des IFRS-Konzernabschlusses der Max Huber Rail Group, wer die Paul Schwarz GmbH & Co. KG (Sitz Augsburg, Gleisbauunternehmen) beherrscht.

Grundlage sind ausschließlich die beigefügten Dokumente: der Gesellschaftsvertrag der Paul Schwarz GmbH & Co. KG (DOKUMENT 1 bis 4, Paragraphen 1 bis 20) sowie die Anlagen zu diesem Vertrag (DOKUMENT 5 und 6: Anlage 1 Genehmigungscheckliste Projektverträge; DOKUMENT 7: Anlage 2 Freigaberegelung; DOKUMENT 8: Anlage 3 Geschäftsordnung für die Geschäftsführer und Prokuristen).

Zitieren Sie die von Ihnen herangezogenen Bestimmungen jeweils mit Paragraph, Absatz und gegebenenfalls Ziffer.

FRAGESTELLUNG:
Der Gesellschafterin Max Huber Rail GmbH stehen besondere Rechte hinsichtlich der Bestellung eines Geschäftsführers und ein Letztentscheidungsrecht in bestimmten Angelegenheiten zu.

Stellen Sie diese Rechte dar und beurteilen Sie, ob sie der Max Huber Rail GmbH Verfügungsgewalt (power) über die maßgeblichen Tätigkeiten im Sinne von IFRS 10.7(a) vermitteln.

### Musterlösung (gold_answer)

Die Rechte ergeben sich aus Paragraph 6 Abs. 8 des Gesellschaftsvertrags. Die Max Huber Rail GmbH und etwaige Rechtsnachfolger haben das Recht, einen Geschäftsführer der Komplementärin vorzuschlagen; die übrigen Gesellschafter sind verpflichtet, dem Vorschlag zuzustimmen, sofern keine erheblichen Gründe in der Person des Vorgeschlagenen entgegenstehen. Ein entsprechendes Vorschlagsrecht steht den Gesellschaftern der Familie Schwarz zu. Das Recht erlischt, wenn die jeweilige Beteiligung weniger als 50 % beträgt.

Der auf Vorschlag der Max Huber Rail GmbH bestellte Geschäftsführer hat ein Letztentscheidungsrecht bei (i) der Teilnahme an Ausschreibungen, (ii) der Beteiligung an Arbeitsgemeinschaften und dem Eingehen von Subunternehmerverhältnissen und (iii) Investitionsentscheidungen innerhalb der bestehenden Budgetplanung. Werden diese Angelegenheiten der Gesellschafterversammlung vorgelegt, steht der Max Huber Rail GmbH auch dort das Letztentscheidungsrecht zu.

Diese Rechte vermitteln keine Verfügungsgewalt über die maßgeblichen Tätigkeiten im Sinne von IFRS 10.7(a). Sie sind zwar substanziell und keine bloßen Schutzrechte, wirken aber ausschließlich innerhalb eines Rahmens, den die Max Huber Rail GmbH nicht selbst setzen kann:
- Die Investitionsentscheidungen sind ausdrücklich auf Entscheidungen 'innerhalb der bestehenden Budgetplanung' beschränkt.
- Die Festlegung des Jahresbudgets ist nach Anlage 3 Paragraph 3 Abs. 1 Nr. 3 ein zustimmungspflichtiges Geschäft und damit den Gesellschaftern vorbehalten; sie erfordert nach Paragraph 9 Abs. 2 Nr. 3 eine Mehrheit von 2/3 der Stimmen der anwesenden und vertretenen stimmberechtigten Kommanditisten, die die Max Huber Rail GmbH mit 50 % der Stimmen nicht allein erreicht.
- Die Teilnahme an Ausschreibungen wird zusätzlich durch den nach Paragraph 6 Abs. 5 verbindlichen Genehmigungsprozess der Anlage 1 begrenzt.
- Der Katalog der zustimmungspflichtigen Geschäfte kann nach Paragraph 6 Abs. 4 von der Gesellschafterversammlung jederzeit erweitert werden, ohne dass es einer Vertragsänderung bedürfte; auch darüber bestimmt die Max Huber Rail GmbH nicht allein.

Die Rechte verschaffen der Max Huber Rail GmbH damit Einfluss auf die Ausführung innerhalb des Budgets, nicht aber die Fähigkeit, die ausschlaggebende maßgebliche Tätigkeit - die Festlegung des Budgets - zu steuern.

### Zugelassene Abweichungen (acceptable_variants)

Die Einordnung der Rechte als substanzielle Rechte (substantive rights) im Sinne von IFRS 10.B22 ff., die aber nicht die maßgebliche Tätigkeit betreffen, ist gleichwertig zur obigen Formulierung. Ebenfalls zutreffend ist der Hinweis, dass das Vorschlagsrecht spiegelbildlich auch der Familie Schwarz zusteht und daher keine einseitige Position begründet, sowie der Hinweis, dass das Letztentscheidungsrecht bei einem Absinken der Beteiligung unter 50 % erlischt.

### Bewertungskriterien (grading_criteria)

Answer must contain: (1) die zutreffende Darstellung des Vorschlagsrechts für einen Geschäftsführer nach Paragraph 6 Abs. 8 einschließlich des Umstands, dass ein spiegelbildliches Recht der Familie Schwarz zusteht. (2) die Aufzählung der drei Angelegenheiten des Letztentscheidungsrechts (Ausschreibungen, ARGEn/Subunternehmerverhältnisse, Investitionsentscheidungen). (3) die entscheidende Feststellung, dass die Investitionsentscheidungen nur 'innerhalb der bestehenden Budgetplanung' getroffen werden können, die Rechte also budgetgebunden sind. (4) das Ergebnis, dass diese Rechte KEINE Verfügungsgewalt über die maßgeblichen Tätigkeiten im Sinne von IFRS 10.7(a) vermitteln. (5) die Begründung, dass die Festlegung des Budgets den Gesellschaftern vorbehalten ist und von der Max Huber Rail GmbH nicht allein herbeigeführt werden kann.

Bewertung: Punkt (3) in Verbindung mit (4) trägt die Aufgabe. Eine Antwort, die aus dem Letztentscheidungsrecht auf Beherrschung schließt, ist im Ergebnis falsch und mit höchstens 15 Punkten zu bewerten. Eine Antwort, die (4) richtig beantwortet, die Budgetgebundenheit nach (3) aber nicht erkennt, ist mit höchstens 45 Punkten zu bewerten. Die Einordnung der Rechte als bloße Schutzrechte (protective rights) ist fachlich unzutreffend und mit Abzug zu bewerten, führt aber nicht allein zu 0 Punkten.


---


## Aufgabe 4 — `20260924_0004`

**Antworttyp:** open_text

### Fragestellung

Sie sind Wirtschaftsprüfer/in und beurteilen für Zwecke des IFRS-Konzernabschlusses der Max Huber Rail Group, wer die Paul Schwarz GmbH & Co. KG (Sitz Augsburg, Gleisbauunternehmen) beherrscht.

Grundlage sind ausschließlich die beigefügten Dokumente: der Gesellschaftsvertrag der Paul Schwarz GmbH & Co. KG (DOKUMENT 1 bis 4, Paragraphen 1 bis 20) sowie die Anlagen zu diesem Vertrag (DOKUMENT 5 und 6: Anlage 1 Genehmigungscheckliste Projektverträge; DOKUMENT 7: Anlage 2 Freigaberegelung; DOKUMENT 8: Anlage 3 Geschäftsordnung für die Geschäftsführer und Prokuristen).

Zitieren Sie die von Ihnen herangezogenen Bestimmungen jeweils mit Paragraph, Absatz und gegebenenfalls Ziffer.

FRAGESTELLUNG:
Wer kann die Festlegung des Jahresbudgets der Paul Schwarz GmbH & Co. KG herbeiführen?

Stellen Sie die maßgebliche Beschlusskette dar: auf welcher Grundlage das Budget zustimmungspflichtig ist, welche Mehrheit erforderlich ist, wie sich die Stimmrechte auf die Gesellschafter verteilen und ob eine einzelne Partei diese Mehrheit allein erreichen kann.

### Musterlösung (gold_answer)

Beschlusskette:

1. Die Festlegung des Jahresbudgets - Umsatz-, Aufwand- und Ergebnisplan, Personalplan, Investitionsplan sowie Finanzplan - ist nach Anlage 3 (Geschäftsordnung für die Geschäftsführer und Prokuristen) Paragraph 3 Abs. 1 Nr. 3 ein zustimmungspflichtiges Geschäft; es darf nur mit Zustimmung der Gesellschafter durchgeführt werden. Die Geschäftsordnung gilt nach Paragraph 6 Abs. 7 des Gesellschaftsvertrags in der jeweils geltenden Fassung.

2. Die Zustimmung zu zustimmungspflichtigen Geschäften erfordert nach Paragraph 9 Abs. 2 Nr. 3 des Gesellschaftsvertrags eine Mehrheit von 2/3 der Stimmen der anwesenden und vertretenen stimmberechtigten Kommanditisten.

3. Stimmrechte: Je 1 EUR des Kapitalkontos gewährt eine Stimme (Paragraph 9 Abs. 4). Das Stimmrecht der Komplementärin ist ausgeschlossen (Paragraph 9 Abs. 5). Die Kommanditanteile betragen nach Paragraph 3 Abs. 2: Max Huber Rail GmbH 625.000,00 EUR, Hannes Schwarz 208.334,00 EUR, Wolfgang Schwarz 208.333,00 EUR und Hannah Schwarz 208.333,00 EUR, insgesamt 1.250.000,00 EUR. Die Max Huber Rail GmbH hält damit genau 50 % der Stimmen, die Gesellschafter der Familie Schwarz zusammen ebenfalls 50 %.

4. Ergebnis: Keine Partei kann die Festlegung des Budgets allein herbeiführen. Die Max Huber Rail GmbH erreicht mit 50 % die erforderlichen 2/3 nicht; die Familie Schwarz erreicht sie mit zusammen 50 % ebenfalls nicht, wenn alle Stimmen anwesend oder vertreten sind. Umgekehrt kann jede der beiden Seiten einen Budgetbeschluss in einer Versammlung mit vollständiger Präsenz blockieren.

5. Zu beachten ist, dass die 2/3-Mehrheit nach Paragraph 9 Abs. 2 auf die anwesenden und vertretenen Stimmen abstellt und nicht auf sämtliche vorhandenen Stimmen. Nach Paragraph 8 Abs. 5 ist eine erste Gesellschafterversammlung nur beschlussfähig, wenn die anwesenden und vertretenen Kommanditisten 2/3 aller Stimmen auf sich vereinigen; eine wegen Beschlussunfähigkeit erneut einberufene zweite Gesellschafterversammlung ist jedoch ohne Rücksicht auf die Zahl der anwesenden und vertretenen Stimmen beschlussfähig. Je nach Präsenz können daher unterschiedliche Gesellschafterkonstellationen die erforderliche Mehrheit erreichen. So genügen etwa die Max Huber Rail GmbH gemeinsam mit einem Gesellschafter der Familie Schwarz (833.334 von 1.250.000 Stimmen, rund 66,7 %); ebenso können in einer zweiten Gesellschafterversammlung, in der die Max Huber Rail GmbH nicht anwesend ist, die Gesellschafter der Familie Schwarz den Beschluss fassen.

### Zugelassene Abweichungen (acceptable_variants)

Die Angabe der Beteiligungsquote als 'genau 50 %', '625.000 von 1.250.000' oder '50 zu 50' ist gleichwertig. Der Hinweis, dass die Feststellung des Jahresabschlusses nach Paragraph 9 Abs. 2 Nr. 6 derselben 2/3-Mehrheit unterliegt, ist zutreffend. Wird Punkt 5 (Abstellen auf die anwesenden und vertretenen Stimmen, beschlussfähige zweite Versammlung) nicht erwähnt, ist die Antwort insoweit unvollständig, im Kern aber nicht falsch.

### Bewertungskriterien (grading_criteria)

Answer must contain: (1) die Feststellung, dass die Festlegung des Jahresbudgets nach Anlage 3 Paragraph 3 Abs. 1 Nr. 3 ein zustimmungspflichtiges Geschäft ist. (2) die erforderliche Mehrheit von 2/3 der Stimmen der anwesenden und vertretenen stimmberechtigten Kommanditisten nach Paragraph 9 Abs. 2 Nr. 3. (3) die Stimmrechtsregel 'je 1 EUR des Kapitalkontos eine Stimme' nach Paragraph 9 Abs. 4 sowie den Ausschluss des Stimmrechts der Komplementärin nach Paragraph 9 Abs. 5. (4) die zutreffende Stimmverteilung: Max Huber Rail GmbH 625.000 von insgesamt 1.250.000 Stimmen, also genau 50 %, Familie Schwarz zusammen ebenfalls 50 %. (5) das Ergebnis, dass keine Partei die Budgetfestlegung allein herbeiführen kann.

Bewertung: Die Verknüpfung von (1) und (2) - also das Auffinden der Kette von der Anlage 3 in den Gesellschaftsvertrag - ist der eigentliche Prüfungsgegenstand. Fehlt diese Verknüpfung, sind höchstens 40 Punkte zu vergeben, auch wenn das Ergebnis (5) zutrifft. Rechenfehler bei der Quote (z. B. 'knapp über 50 %' statt 'genau 50 %') führen zu geringem Abzug, nicht zu 0 Punkten. Die zusätzlich richtige Darstellung des Präsenzbezugs der Mehrheit und der beschlussfähigen zweiten Gesellschafterversammlung nach Paragraph 8 Abs. 5 ist mit voller Punktzahl zu honorieren, aber für 100 Punkte nicht zwingend erforderlich.


---


## Aufgabe 5 — `20260924_0005`

**Antworttyp:** open_text

### Fragestellung

Sie sind Wirtschaftsprüfer/in und beurteilen für Zwecke des IFRS-Konzernabschlusses der Max Huber Rail Group, wer die Paul Schwarz GmbH & Co. KG (Sitz Augsburg, Gleisbauunternehmen) beherrscht.

Grundlage sind ausschließlich die beigefügten Dokumente: der Gesellschaftsvertrag der Paul Schwarz GmbH & Co. KG (DOKUMENT 1 bis 4, Paragraphen 1 bis 20) sowie die Anlagen zu diesem Vertrag (DOKUMENT 5 und 6: Anlage 1 Genehmigungscheckliste Projektverträge; DOKUMENT 7: Anlage 2 Freigaberegelung; DOKUMENT 8: Anlage 3 Geschäftsordnung für die Geschäftsführer und Prokuristen).

Zitieren Sie die von Ihnen herangezogenen Bestimmungen jeweils mit Paragraph, Absatz und gegebenenfalls Ziffer.

FRAGESTELLUNG:
Liegt hinsichtlich der Paul Schwarz GmbH & Co. KG eine gemeinschaftliche Führung (joint control) im Sinne von IFRS 11 vor?

Beurteilen Sie dies unter Berücksichtigung der Beschlussfassung über das Jahresbudget und begründen Sie Ihr Ergebnis.

### Musterlösung (gold_answer)

Nein, eine gemeinschaftliche Führung liegt nicht vor.

Gemeinschaftliche Führung setzt nach IFRS 11.7 die vertraglich vereinbarte Teilhabe an der Führung voraus, die nur dann besteht, wenn Entscheidungen über die maßgeblichen Tätigkeiten die einstimmige Zustimmung der die Führung gemeinsam ausübenden Parteien erfordern. Erforderlich ist also, dass sich aus der vertraglichen Vereinbarung eine bestimmte, feststehende Gruppe von Parteien ergibt, deren Zustimmung stets notwendig ist.

Daran fehlt es hier. Die Zustimmung zur Festlegung des Jahresbudgets erfordert nach Paragraph 9 Abs. 2 Nr. 3 eine Mehrheit von 2/3 der Stimmen der anwesenden und vertretenen stimmberechtigten Kommanditisten. Die Mehrheit bezieht sich damit nicht auf sämtliche vorhandenen Stimmen, sondern auf die jeweilige Präsenz. Nach Paragraph 8 Abs. 5 ist zudem eine wegen Beschlussunfähigkeit erneut einberufene zweite Gesellschafterversammlung ohne Rücksicht auf die Zahl der anwesenden und vertretenen Stimmen beschlussfähig.

Infolgedessen können unterschiedliche Gesellschafterkonstellationen die erforderliche Mehrheit erreichen:
- Die Max Huber Rail GmbH gemeinsam mit einem der drei Gesellschafter der Familie Schwarz vereinigt 833.334 von 1.250.000 Stimmen und damit rund 66,7 % auf sich.
- In einer zweiten Gesellschafterversammlung, in der die Max Huber Rail GmbH nicht anwesend oder vertreten ist, können die Gesellschafter der Familie Schwarz den Beschluss allein fassen.

Es gibt somit keine vertraglich festgelegte Kombination von Parteien, deren Zustimmung zwingend erforderlich wäre. Die Voraussetzung der einstimmigen Zustimmung bestimmter Parteien ist nicht erfüllt, sodass weder eine gemeinschaftliche Tätigkeit (joint operation) noch ein Gemeinschaftsunternehmen (joint venture) im Sinne von IFRS 11 vorliegt.

### Zugelassene Abweichungen (acceptable_variants)

Der Verweis auf IFRS 11.B5 bis B11 statt auf IFRS 11.7 ist gleichwertig. Die Begründung ist auch dann vollständig, wenn sie nur auf den Präsenzbezug der 2/3-Mehrheit abstellt und die beschlussfähige zweite Gesellschafterversammlung nicht gesondert erwähnt, solange das Argument der wechselnden Gesellschafterkonstellationen klar herausgearbeitet wird. Die zusätzliche Feststellung, dass mangels gemeinschaftlicher Führung auch keine Einordnung als joint operation oder joint venture in Betracht kommt, ist zutreffend.

### Bewertungskriterien (grading_criteria)

Answer must contain: (1) das Ergebnis, dass KEINE gemeinschaftliche Führung vorliegt. (2) die zutreffende Wiedergabe des Maßstabs: gemeinschaftliche Führung erfordert, dass Entscheidungen über die maßgeblichen Tätigkeiten die einstimmige Zustimmung bestimmter, vertraglich festgelegter Parteien voraussetzen. (3) die tragende Begründung, dass hier keine solche feststehende Parteienkombination existiert, weil unterschiedliche Gesellschafterkonstellationen die erforderliche 2/3-Mehrheit erreichen können. (4) mindestens ein konkretes Beispiel einer solchen Konstellation, etwa Max Huber Rail GmbH gemeinsam mit einem Schwarz-Gesellschafter (rund 66,7 %) oder die Familie Schwarz in einer beschlussfähigen zweiten Gesellschafterversammlung.

Bewertung: Wird gemeinschaftliche Führung bejaht - etwa mit dem Argument, die 50/50-Verteilung führe zu wechselseitigen Vetorechten und damit zu joint control - ist die Antwort im Ergebnis falsch: höchstens 15 Punkte. Dieser Fehler ist die naheliegendste Fehleinschätzung des Falles und darf nicht mit Teilpunkten für eine ansonsten saubere IFRS-11-Darstellung ausgeglichen werden. Wird (1) richtig beantwortet, die Begründung (3) aber nicht auf die wechselnden Konstellationen gestützt, sind höchstens 50 Punkte zu vergeben. Volle Punktzahl nur bei (1) bis (3); (4) ist für mehr als 85 Punkte erforderlich.


---


## Aufgabe 6 — `20260924_0006`

**Antworttyp:** open_text

### Fragestellung

Sie sind Wirtschaftsprüfer/in und beurteilen für Zwecke des IFRS-Konzernabschlusses der Max Huber Rail Group, wer die Paul Schwarz GmbH & Co. KG (Sitz Augsburg, Gleisbauunternehmen) beherrscht.

Grundlage sind ausschließlich die beigefügten Dokumente: der Gesellschaftsvertrag der Paul Schwarz GmbH & Co. KG (DOKUMENT 1 bis 4, Paragraphen 1 bis 20) sowie die Anlagen zu diesem Vertrag (DOKUMENT 5 und 6: Anlage 1 Genehmigungscheckliste Projektverträge; DOKUMENT 7: Anlage 2 Freigaberegelung; DOKUMENT 8: Anlage 3 Geschäftsordnung für die Geschäftsführer und Prokuristen).

Zitieren Sie die von Ihnen herangezogenen Bestimmungen jeweils mit Paragraph, Absatz und gegebenenfalls Ziffer.

FRAGESTELLUNG:
Welche Konsequenz ergibt sich aus Ihrer Beurteilung für die Abbildung der Beteiligung an der Paul Schwarz GmbH & Co. KG im IFRS-Konzernabschluss der Max Huber Rail Group?

Geben Sie den anzuwendenden Standard und die Bewertungsmethode an und gehen Sie auf etwaige Angabepflichten ein.

### Musterlösung (gold_answer)

Da die Max Huber Rail GmbH die Paul Schwarz GmbH & Co. KG nicht beherrscht, ist diese nicht als Tochterunternehmen nach IFRS 10 in den Konzernabschluss einzubeziehen; eine Vollkonsolidierung scheidet aus. Da auch keine gemeinschaftliche Führung besteht, liegt keine gemeinsame Vereinbarung nach IFRS 11 vor; eine Bilanzierung als joint operation oder als joint venture kommt ebenfalls nicht in Betracht.

Die Max Huber Rail GmbH verfügt jedoch über maßgeblichen Einfluss im Sinne von IAS 28.3 in Verbindung mit IAS 28.5 und IAS 28.6. Dafür sprechen ihre 50 % der Stimmrechte, das Recht zur Benennung eines Geschäftsführers der Komplementärin (Paragraph 6 Abs. 8), das Letztentscheidungsrecht in operativen Angelegenheiten sowie die Möglichkeit, zustimmungspflichtige Geschäfte einschließlich der Budgetfestlegung zu blockieren. Die Beteiligung ist daher als assoziiertes Unternehmen einzustufen und nach IAS 28.16 nach der Equity-Methode zu bilanzieren, sofern keine Befreiung nach IAS 28.17 ff. eingreift.

Angabepflichten: Die Einschätzung, dass trotz eines Stimmrechtsanteils von 50 % und besonderer Entscheidungsrechte keine Beherrschung und keine gemeinschaftliche Führung vorliegt, ist eine wesentliche Ermessensentscheidung, die nach IFRS 12.7 in Verbindung mit IFRS 12.9 anzugeben und zu begründen ist. Hinzu treten die Angaben zu Anteilen an assoziierten Unternehmen nach IFRS 12.20 ff.

### Zugelassene Abweichungen (acceptable_variants)

Der Verweis auf die Equity-Methode ohne Nennung der konkreten Randnummer ist gleichwertig. Der Hinweis, dass die Einstufung als assoziiertes Unternehmen eine Ermessensentscheidung ist und alternativ - bei abweichender Würdigung des maßgeblichen Einflusses - eine Bilanzierung nach IFRS 9 in Betracht käme, ist als Nebenerwägung zulässig, sofern die Equity-Methode als das zutreffende Ergebnis benannt wird. Angaben zu Angabepflichten nach IFRS 12 sind verdienstvoll, aber nicht zwingend.

### Bewertungskriterien (grading_criteria)

Answer must contain: (1) die Feststellung, dass keine Vollkonsolidierung nach IFRS 10 erfolgt. (2) die Feststellung, dass mangels gemeinschaftlicher Führung auch keine Bilanzierung als gemeinsame Vereinbarung nach IFRS 11 in Betracht kommt. (3) die Bejahung eines maßgeblichen Einflusses und die Einstufung als assoziiertes Unternehmen nach IAS 28. (4) die Equity-Methode als anzuwendende Bilanzierungsmethode.

Bewertung: (1), (3) und (4) sind erforderlich. Fehlt (2), sind höchstens 75 Punkte zu vergeben. Wird eine Vollkonsolidierung oder eine Quotenkonsolidierung als Ergebnis genannt, ist die Antwort im Ergebnis falsch: höchstens 10 Punkte. Die Quotenkonsolidierung ist nach IFRS 11 ohnehin nicht mehr zulässig; ihre Nennung ist ein eigenständiger Fehler. Angaben zu IFRS 12 sind zusätzlich verdienstvoll und dürfen nicht als Abschweifung gewertet werden.


---


## Aufgabe 7 — `20260924_0007`

**Antworttyp:** open_text

### Fragestellung

Sie sind Wirtschaftsprüfer/in und beurteilen für Zwecke des IFRS-Konzernabschlusses der Max Huber Rail Group, wer die Paul Schwarz GmbH & Co. KG (Sitz Augsburg, Gleisbauunternehmen) beherrscht.

Grundlage sind ausschließlich die beigefügten Dokumente: der Gesellschaftsvertrag der Paul Schwarz GmbH & Co. KG (DOKUMENT 1 bis 4, Paragraphen 1 bis 20) sowie die Anlagen zu diesem Vertrag (DOKUMENT 5 und 6: Anlage 1 Genehmigungscheckliste Projektverträge; DOKUMENT 7: Anlage 2 Freigaberegelung; DOKUMENT 8: Anlage 3 Geschäftsordnung für die Geschäftsführer und Prokuristen).

Zitieren Sie die von Ihnen herangezogenen Bestimmungen jeweils mit Paragraph, Absatz und gegebenenfalls Ziffer.

FRAGESTELLUNG:
Erstellen Sie eine zusammenhängende fachliche Stellungnahme zu der Frage, wer die Paul Schwarz GmbH & Co. KG nach IFRS 10 beherrscht.

Gehen Sie dabei strukturiert vor und behandeln Sie mindestens: die Gesellschafter- und Stimmrechtsstruktur, die Rolle der Komplementärin, die maßgeblichen Tätigkeiten und die für die Beurteilung ausschlaggebende Tätigkeit, die besonderen Entscheidungsrechte der Max Huber Rail GmbH und ihre Reichweite, die Beschlussfassung über das Jahresbudget einschließlich der erforderlichen Mehrheiten, die Frage einer gemeinschaftlichen Führung nach IFRS 11 sowie das Ergebnis und dessen Konsequenz für den Konzernabschluss der Max Huber Rail Group.

### Musterlösung (gold_answer)

1. Gesellschafter- und Stimmrechtsstruktur
Persönlich haftende Gesellschafterin ist die AB Gleisbau GmbH, die zu einer Einlage weder verpflichtet noch berechtigt ist (Paragraph 3 Abs. 1). Kommanditisten sind nach Paragraph 3 Abs. 2 die Max Huber Rail GmbH mit 625.000,00 EUR, Hannes Schwarz mit 208.334,00 EUR, Wolfgang Schwarz mit 208.333,00 EUR und Hannah Schwarz mit 208.333,00 EUR, insgesamt 1.250.000,00 EUR. Je 1 EUR des Kapitalkontos gewährt eine Stimme (Paragraph 9 Abs. 4); das Stimmrecht der Komplementärin ist ausgeschlossen (Paragraph 9 Abs. 5). Die Max Huber Rail GmbH hält damit genau 50 % der Stimmen, die Gesellschafter der Familie Schwarz zusammen ebenfalls 50 %.

2. Rolle der Komplementärin
Zur Geschäftsführung und Vertretung ist die Komplementärin allein berechtigt und verpflichtet (Paragraph 6 Abs. 1). Sie beherrscht die Gesellschaft gleichwohl nicht: Sie hält keine Kapitaleinlage, hat kein Stimmrecht und ist am Gesellschaftsvermögen sowie am Gewinn und Verlust nicht beteiligt (Paragraph 3 Abs. 1, Paragraph 9 Abs. 5, Paragraph 10 Abs. 4). Sie unterliegt zudem einem umfangreichen Katalog zustimmungspflichtiger Geschäfte (Paragraph 6 Abs. 3), den die Gesellschafterversammlung jederzeit erweitern kann (Paragraph 6 Abs. 4), sowie den verbindlichen Anlagen 1 bis 3 (Paragraph 6 Abs. 5 bis 7). Sie handelt damit als Agent im Sinne von IFRS 10.B58 ff. und nicht als Prinzipal.

3. Maßgebliche Tätigkeiten und ausschlaggebende Tätigkeit
Maßgeblich sind die renditewesentlichen operativen Tätigkeiten des Gleisbaugeschäfts, insbesondere die Teilnahme an Ausschreibungen, die Beteiligung an Arbeitsgemeinschaften und das Eingehen von Subunternehmerverhältnissen sowie Investitionsentscheidungen. Uebergeordnet steht die Festlegung des Jahresbudgets, das nach Anlage 3 Paragraph 3 Abs. 1 Nr. 3 den Umsatz-, Aufwand- und Ergebnisplan, den Personalplan, den Investitionsplan und den Finanzplan umfasst. Ausschlaggebend ist die Festlegung des Jahresbudgets, weil die operativen Entscheidungsrechte nur innerhalb des dadurch gesetzten Rahmens ausgeübt werden können.

4. Besondere Entscheidungsrechte der Max Huber Rail GmbH und ihre Reichweite
Nach Paragraph 6 Abs. 8 kann die Max Huber Rail GmbH einen Geschäftsführer der Komplementärin vorschlagen; ein spiegelbildliches Recht steht den Gesellschaftern der Familie Schwarz zu, und das Recht erlischt bei einem Absinken der Beteiligung unter 50 %. Der auf ihren Vorschlag bestellte Geschäftsführer hat ein Letztentscheidungsrecht bei der Teilnahme an Ausschreibungen, der Beteiligung an Arbeitsgemeinschaften und dem Eingehen von Subunternehmerverhältnissen sowie bei Investitionsentscheidungen innerhalb der bestehenden Budgetplanung; dieses Recht gilt auch in der Gesellschafterversammlung. Die Rechte sind substanziell, aber budgetgebunden: Die Investitionsentscheidungen sind ausdrücklich auf den bestehenden Budgetrahmen beschränkt, und die Teilnahme an Ausschreibungen wird zusätzlich durch den nach Paragraph 6 Abs. 5 verbindlichen Genehmigungsprozess der Anlage 1 begrenzt, der weder der Disposition der Gesellschaft noch der Gesellschafter oder Geschäftsführer unterliegt.

5. Beschlussfassung über das Jahresbudget
Die Festlegung des Jahresbudgets ist nach Anlage 3 Paragraph 3 Abs. 1 Nr. 3 ein zustimmungspflichtiges Geschäft. Die Zustimmung zu zustimmungspflichtigen Geschäften erfordert nach Paragraph 9 Abs. 2 Nr. 3 eine Mehrheit von 2/3 der Stimmen der anwesenden und vertretenen stimmberechtigten Kommanditisten. Mit 50 % der Stimmen kann die Max Huber Rail GmbH diese Mehrheit nicht allein erreichen; sie kann einen Budgetbeschluss bei vollständiger Präsenz allerdings blockieren. Dasselbe gilt spiegelbildlich für die Familie Schwarz.

6. Gemeinschaftliche Führung nach IFRS 11
Eine gemeinschaftliche Führung liegt nicht vor. Sie setzt voraus, dass Entscheidungen über die maßgeblichen Tätigkeiten die einstimmige Zustimmung bestimmter, vertraglich festgelegter Parteien erfordern. Die 2/3-Mehrheit nach Paragraph 9 Abs. 2 stellt jedoch auf die anwesenden und vertretenen Stimmen ab, und eine wegen Beschlussunfähigkeit erneut einberufene zweite Gesellschafterversammlung ist nach Paragraph 8 Abs. 5 ohne Rücksicht auf die Präsenz beschlussfähig. Dadurch können unterschiedliche Gesellschafterkonstellationen die erforderliche Mehrheit erreichen - etwa die Max Huber Rail GmbH gemeinsam mit einem Schwarz-Gesellschafter mit 833.334 von 1.250.000 Stimmen (rund 66,7 %) oder die Gesellschafter der Familie Schwarz in einer zweiten Gesellschafterversammlung. Eine feststehende Gruppe von Parteien, deren Zustimmung stets erforderlich wäre, existiert somit nicht.

7. Ergebnis und Konsequenz
Keine Partei beherrscht die Paul Schwarz GmbH & Co. KG. Weder liegt Alleinbeherrschung nach IFRS 10 vor noch eine gemeinschaftliche Führung nach IFRS 11. Die Gesellschaft ist daher nicht in den Konzernabschluss der Max Huber Rail Group zu konsolidieren. Die Max Huber Rail GmbH verfügt jedoch über maßgeblichen Einfluss nach IAS 28; die Beteiligung ist als assoziiertes Unternehmen nach der Equity-Methode zu bilanzieren. Die Einschätzung, dass trotz 50 % der Stimmrechte und besonderer Entscheidungsrechte keine Beherrschung vorliegt, ist eine wesentliche Ermessensentscheidung und nach IFRS 12.7 in Verbindung mit IFRS 12.9 anzugeben.

### Zugelassene Abweichungen (acceptable_variants)

Eine abweichende Gliederung ist unerheblich, solange die geforderten Punkte inhaltlich behandelt werden. Die Einordnung der Komplementärin als Agent kann auch ohne ausdrückliche Nennung von IFRS 10.B58 ff. erfolgen, sofern die Begründung (keine Einlage, kein Stimmrecht, keine Ergebnisbeteiligung, umfassende Zustimmungsvorbehalte) trägt. Der Hinweis, dass die Beurteilung bei einer Veränderung der Beteiligungsverhältnisse oder einer Aenderung des Katalogs zustimmungspflichtiger Geschäfte neu vorzunehmen wäre, ist zutreffend.

### Bewertungskriterien (grading_criteria)

Answer must contain: (1) die zutreffende Stimmrechtsstruktur einschließlich der Regel 'je 1 EUR eine Stimme' und des Ergebnisses von genau 50 % für die Max Huber Rail GmbH. (2) die Feststellung, dass die Komplementärin trotz alleiniger Geschäftsführungsbefugnis nicht beherrscht, weil sie ohne Kapitalbeteiligung, Stimmrecht und Ergebnisbeteiligung handelt. (3) die Identifikation der Festlegung des Jahresbudgets als ausschlaggebende maßgebliche Tätigkeit. (4) die Feststellung, dass die besonderen Entscheidungsrechte der Max Huber Rail GmbH nach Paragraph 6 Abs. 8 nur innerhalb des Budgetrahmens bestehen. (5) die Beschlusskette von Anlage 3 Paragraph 3 Abs. 1 Nr. 3 zu Paragraph 9 Abs. 2 Nr. 3 mit der erforderlichen 2/3-Mehrheit. (6) die Verneinung der gemeinschaftlichen Führung nach IFRS 11 mit der Begründung wechselnder Gesellschafterkonstellationen. (7) das Ergebnis, dass keine Partei beherrscht. (8) die Konsequenz: keine Konsolidierung, sondern Einstufung als assoziiertes Unternehmen und Bilanzierung nach der Equity-Methode gemäß IAS 28.

Bewertung: (7) ist zwingend. Wird eine andere Partei als beherrschend benannt, sind höchstens 15 Punkte zu vergeben. Die Punkte (3), (4) und (5) bilden gemeinsam die eigentliche fachliche Leistung; fehlen sie sämtlich, sind trotz zutreffendem Ergebnis höchstens 40 Punkte zu vergeben, weil das richtige Ergebnis dann nicht hergeleitet, sondern nur behauptet ist. Für mehr als 85 Punkte sind (3) bis (7) erforderlich. Wird (6) unzutreffend beantwortet, also gemeinschaftliche Führung bejaht, sind höchstens 45 Punkte zu vergeben. Ein höherer Detailgrad bei den übrigen Gliederungspunkten kann fehlende Kernpunkte nicht ausgleichen.


---


## Aufgabe 8 — `20260924_0008`

**Antworttyp:** open_text

### Fragestellung

Sie sind Wirtschaftsprüfer/in und beurteilen für Zwecke des IFRS-Konzernabschlusses der Max Huber Rail Group, wer die Paul Schwarz GmbH & Co. KG (Sitz Augsburg, Gleisbauunternehmen) beherrscht.

Grundlage sind ausschließlich die beigefügten Dokumente: der Gesellschaftsvertrag der Paul Schwarz GmbH & Co. KG (DOKUMENT 1 bis 4, Paragraphen 1 bis 20) sowie die Anlagen zu diesem Vertrag (DOKUMENT 5 und 6: Anlage 1 Genehmigungscheckliste Projektverträge; DOKUMENT 7: Anlage 2 Freigaberegelung; DOKUMENT 8: Anlage 3 Geschäftsordnung für die Geschäftsführer und Prokuristen).

Zitieren Sie die von Ihnen herangezogenen Bestimmungen jeweils mit Paragraph, Absatz und gegebenenfalls Ziffer.

FRAGESTELLUNG:
Beantworten Sie die folgenden sechs Teilfragen vollständig und in der angegebenen Reihenfolge. Gliedern Sie Ihre Antwort nach den Teilfragen und kennzeichnen Sie jede Teilantwort mit ihrer Nummer.

TEILFRAGE 1 - Maßgebliche Tätigkeiten:
Welches sind die maßgeblichen Tätigkeiten (relevant activities) der Paul Schwarz GmbH & Co. KG im Sinne von IFRS 10.10 ff., und welche dieser Tätigkeiten ist für die Beurteilung der Beherrschung letztlich ausschlaggebend?

Begründen Sie, warum gerade diese Tätigkeit den Ausschlag gibt.

TEILFRAGE 2 - Besondere Entscheidungsrechte der Max Huber Rail GmbH:
Der Gesellschafterin Max Huber Rail GmbH stehen besondere Rechte hinsichtlich der Bestellung eines Geschäftsführers und ein Letztentscheidungsrecht in bestimmten Angelegenheiten zu.

Stellen Sie diese Rechte dar und beurteilen Sie, ob sie der Max Huber Rail GmbH Verfügungsgewalt (power) über die maßgeblichen Tätigkeiten im Sinne von IFRS 10.7(a) vermitteln.

TEILFRAGE 3 - Festlegung des Jahresbudgets:
Wer kann die Festlegung des Jahresbudgets der Paul Schwarz GmbH & Co. KG herbeiführen?

Stellen Sie die maßgebliche Beschlusskette dar: auf welcher Grundlage das Budget zustimmungspflichtig ist, welche Mehrheit erforderlich ist, wie sich die Stimmrechte auf die Gesellschafter verteilen und ob eine einzelne Partei diese Mehrheit allein erreichen kann.

TEILFRAGE 4 - Gemeinschaftliche Führung nach IFRS 11:
Liegt hinsichtlich der Paul Schwarz GmbH & Co. KG eine gemeinschaftliche Führung (joint control) im Sinne von IFRS 11 vor?

Beurteilen Sie dies unter Berücksichtigung der Beschlussfassung über das Jahresbudget und begründen Sie Ihr Ergebnis.

TEILFRAGE 5 - Ergebnis: Beherrschung nach IFRS 10:
Welche Partei beherrscht die Paul Schwarz GmbH & Co. KG im Sinne von IFRS 10?

Antworten Sie in höchstens drei Sätzen. Nennen Sie entweder die beherrschende Partei oder stellen Sie fest, dass keine Partei beherrscht, und begründen Sie das Ergebnis knapp. Gehen Sie dabei ausdrücklich sowohl auf eine Alleinbeherrschung nach IFRS 10 als auch auf eine gemeinschaftliche Führung nach IFRS 11 ein.

TEILFRAGE 6 - Konsequenz für den Konzernabschluss:
Welche Konsequenz ergibt sich aus Ihrer Beurteilung für die Abbildung der Beteiligung an der Paul Schwarz GmbH & Co. KG im IFRS-Konzernabschluss der Max Huber Rail Group?

Geben Sie den anzuwendenden Standard und die Bewertungsmethode an und gehen Sie auf etwaige Angabepflichten ein.

### Musterlösung (gold_answer)

TEILFRAGE 1 - Maßgebliche Tätigkeiten

Maßgebliche Tätigkeiten sind die Tätigkeiten, die die Rendite der Gesellschaft wesentlich beeinflussen, also das operative Gleisbaugeschäft: insbesondere die Teilnahme an Ausschreibungen, die Beteiligung an Arbeitsgemeinschaften und das Eingehen von Subunternehmerverhältnissen sowie Investitionsentscheidungen (Paragraph 6 Abs. 8 des Gesellschaftsvertrags). Hinzu tritt als übergeordnete Steuerungsentscheidung die Festlegung des Jahresbudgets, das nach Anlage 3 Paragraph 3 Abs. 1 Nr. 3 den Umsatz-, Aufwand- und Ergebnisplan, den Personalplan, den Investitionsplan und den Finanzplan umfasst.

Ausschlaggebend ist die Festlegung des Jahresbudgets. Die operativen Entscheidungsrechte, die der Max Huber Rail GmbH zustehen, können nach dem Wortlaut des Paragraph 6 Abs. 8 nur innerhalb des bestehenden Budgets ausgeübt werden - Investitionsentscheidungen ausdrücklich nur 'innerhalb der bestehenden Budgetplanung'. Zusätzlich wird die Teilnahme an Ausschreibungen durch den nach Paragraph 6 Abs. 5 verbindlichen Genehmigungsprozess der Anlage 1 begrenzt, der weder der Disposition der Gesellschaft noch der Gesellschafter oder Geschäftsführer unterliegt und Projekte oberhalb bestimmter Schwellen der Genehmigung durch Marktverantwortlichen, CEO oder Oberste Leitung der Max Huber Rail Group unterwirft.

Wer das Budget bestimmt, setzt damit den Rahmen für sämtliche übrigen maßgeblichen Tätigkeiten. Die Beherrschungsfrage entscheidet sich daher daran, wer über die Festlegung des Jahresbudgets bestimmen kann, und nicht daran, wer die operativen Einzelentscheidungen innerhalb dieses Rahmens trifft.


TEILFRAGE 2 - Besondere Entscheidungsrechte der Max Huber Rail GmbH

Die Rechte ergeben sich aus Paragraph 6 Abs. 8 des Gesellschaftsvertrags. Die Max Huber Rail GmbH und etwaige Rechtsnachfolger haben das Recht, einen Geschäftsführer der Komplementärin vorzuschlagen; die übrigen Gesellschafter sind verpflichtet, dem Vorschlag zuzustimmen, sofern keine erheblichen Gründe in der Person des Vorgeschlagenen entgegenstehen. Ein entsprechendes Vorschlagsrecht steht den Gesellschaftern der Familie Schwarz zu. Das Recht erlischt, wenn die jeweilige Beteiligung weniger als 50 % beträgt.

Der auf Vorschlag der Max Huber Rail GmbH bestellte Geschäftsführer hat ein Letztentscheidungsrecht bei (i) der Teilnahme an Ausschreibungen, (ii) der Beteiligung an Arbeitsgemeinschaften und dem Eingehen von Subunternehmerverhältnissen und (iii) Investitionsentscheidungen innerhalb der bestehenden Budgetplanung. Werden diese Angelegenheiten der Gesellschafterversammlung vorgelegt, steht der Max Huber Rail GmbH auch dort das Letztentscheidungsrecht zu.

Diese Rechte vermitteln keine Verfügungsgewalt über die maßgeblichen Tätigkeiten im Sinne von IFRS 10.7(a). Sie sind zwar substanziell und keine bloßen Schutzrechte, wirken aber ausschließlich innerhalb eines Rahmens, den die Max Huber Rail GmbH nicht selbst setzen kann:
- Die Investitionsentscheidungen sind ausdrücklich auf Entscheidungen 'innerhalb der bestehenden Budgetplanung' beschränkt.
- Die Festlegung des Jahresbudgets ist nach Anlage 3 Paragraph 3 Abs. 1 Nr. 3 ein zustimmungspflichtiges Geschäft und damit den Gesellschaftern vorbehalten; sie erfordert nach Paragraph 9 Abs. 2 Nr. 3 eine Mehrheit von 2/3 der Stimmen der anwesenden und vertretenen stimmberechtigten Kommanditisten, die die Max Huber Rail GmbH mit 50 % der Stimmen nicht allein erreicht.
- Die Teilnahme an Ausschreibungen wird zusätzlich durch den nach Paragraph 6 Abs. 5 verbindlichen Genehmigungsprozess der Anlage 1 begrenzt.
- Der Katalog der zustimmungspflichtigen Geschäfte kann nach Paragraph 6 Abs. 4 von der Gesellschafterversammlung jederzeit erweitert werden, ohne dass es einer Vertragsänderung bedürfte; auch darüber bestimmt die Max Huber Rail GmbH nicht allein.

Die Rechte verschaffen der Max Huber Rail GmbH damit Einfluss auf die Ausführung innerhalb des Budgets, nicht aber die Fähigkeit, die ausschlaggebende maßgebliche Tätigkeit - die Festlegung des Budgets - zu steuern.


TEILFRAGE 3 - Festlegung des Jahresbudgets

Beschlusskette:

1. Die Festlegung des Jahresbudgets - Umsatz-, Aufwand- und Ergebnisplan, Personalplan, Investitionsplan sowie Finanzplan - ist nach Anlage 3 (Geschäftsordnung für die Geschäftsführer und Prokuristen) Paragraph 3 Abs. 1 Nr. 3 ein zustimmungspflichtiges Geschäft; es darf nur mit Zustimmung der Gesellschafter durchgeführt werden. Die Geschäftsordnung gilt nach Paragraph 6 Abs. 7 des Gesellschaftsvertrags in der jeweils geltenden Fassung.

2. Die Zustimmung zu zustimmungspflichtigen Geschäften erfordert nach Paragraph 9 Abs. 2 Nr. 3 des Gesellschaftsvertrags eine Mehrheit von 2/3 der Stimmen der anwesenden und vertretenen stimmberechtigten Kommanditisten.

3. Stimmrechte: Je 1 EUR des Kapitalkontos gewährt eine Stimme (Paragraph 9 Abs. 4). Das Stimmrecht der Komplementärin ist ausgeschlossen (Paragraph 9 Abs. 5). Die Kommanditanteile betragen nach Paragraph 3 Abs. 2: Max Huber Rail GmbH 625.000,00 EUR, Hannes Schwarz 208.334,00 EUR, Wolfgang Schwarz 208.333,00 EUR und Hannah Schwarz 208.333,00 EUR, insgesamt 1.250.000,00 EUR. Die Max Huber Rail GmbH hält damit genau 50 % der Stimmen, die Gesellschafter der Familie Schwarz zusammen ebenfalls 50 %.

4. Ergebnis: Keine Partei kann die Festlegung des Budgets allein herbeiführen. Die Max Huber Rail GmbH erreicht mit 50 % die erforderlichen 2/3 nicht; die Familie Schwarz erreicht sie mit zusammen 50 % ebenfalls nicht, wenn alle Stimmen anwesend oder vertreten sind. Umgekehrt kann jede der beiden Seiten einen Budgetbeschluss in einer Versammlung mit vollständiger Präsenz blockieren.

5. Zu beachten ist, dass die 2/3-Mehrheit nach Paragraph 9 Abs. 2 auf die anwesenden und vertretenen Stimmen abstellt und nicht auf sämtliche vorhandenen Stimmen. Nach Paragraph 8 Abs. 5 ist eine erste Gesellschafterversammlung nur beschlussfähig, wenn die anwesenden und vertretenen Kommanditisten 2/3 aller Stimmen auf sich vereinigen; eine wegen Beschlussunfähigkeit erneut einberufene zweite Gesellschafterversammlung ist jedoch ohne Rücksicht auf die Zahl der anwesenden und vertretenen Stimmen beschlussfähig. Je nach Präsenz können daher unterschiedliche Gesellschafterkonstellationen die erforderliche Mehrheit erreichen. So genügen etwa die Max Huber Rail GmbH gemeinsam mit einem Gesellschafter der Familie Schwarz (833.334 von 1.250.000 Stimmen, rund 66,7 %); ebenso können in einer zweiten Gesellschafterversammlung, in der die Max Huber Rail GmbH nicht anwesend ist, die Gesellschafter der Familie Schwarz den Beschluss fassen.


TEILFRAGE 4 - Gemeinschaftliche Führung nach IFRS 11

Nein, eine gemeinschaftliche Führung liegt nicht vor.

Gemeinschaftliche Führung setzt nach IFRS 11.7 die vertraglich vereinbarte Teilhabe an der Führung voraus, die nur dann besteht, wenn Entscheidungen über die maßgeblichen Tätigkeiten die einstimmige Zustimmung der die Führung gemeinsam ausübenden Parteien erfordern. Erforderlich ist also, dass sich aus der vertraglichen Vereinbarung eine bestimmte, feststehende Gruppe von Parteien ergibt, deren Zustimmung stets notwendig ist.

Daran fehlt es hier. Die Zustimmung zur Festlegung des Jahresbudgets erfordert nach Paragraph 9 Abs. 2 Nr. 3 eine Mehrheit von 2/3 der Stimmen der anwesenden und vertretenen stimmberechtigten Kommanditisten. Die Mehrheit bezieht sich damit nicht auf sämtliche vorhandenen Stimmen, sondern auf die jeweilige Präsenz. Nach Paragraph 8 Abs. 5 ist zudem eine wegen Beschlussunfähigkeit erneut einberufene zweite Gesellschafterversammlung ohne Rücksicht auf die Zahl der anwesenden und vertretenen Stimmen beschlussfähig.

Infolgedessen können unterschiedliche Gesellschafterkonstellationen die erforderliche Mehrheit erreichen:
- Die Max Huber Rail GmbH gemeinsam mit einem der drei Gesellschafter der Familie Schwarz vereinigt 833.334 von 1.250.000 Stimmen und damit rund 66,7 % auf sich.
- In einer zweiten Gesellschafterversammlung, in der die Max Huber Rail GmbH nicht anwesend oder vertreten ist, können die Gesellschafter der Familie Schwarz den Beschluss allein fassen.

Es gibt somit keine vertraglich festgelegte Kombination von Parteien, deren Zustimmung zwingend erforderlich wäre. Die Voraussetzung der einstimmigen Zustimmung bestimmter Parteien ist nicht erfüllt, sodass weder eine gemeinschaftliche Tätigkeit (joint operation) noch ein Gemeinschaftsunternehmen (joint venture) im Sinne von IFRS 11 vorliegt.


TEILFRAGE 5 - Ergebnis: Beherrschung nach IFRS 10

Keine Partei beherrscht die Paul Schwarz GmbH & Co. KG.

Eine Alleinbeherrschung nach IFRS 10 liegt nicht vor: Die Max Huber Rail GmbH verfügt zwar über besondere Entscheidungsrechte (Paragraph 6 Abs. 8 des Gesellschaftsvertrags), kann diese aber nur innerhalb des durch das Jahresbudget vorgegebenen Rahmens ausüben. Entscheidend ist daher, wer das Budget festlegen kann; die Festlegung des Jahresbudgets ist nach Anlage 3 Paragraph 3 Abs. 1 Nr. 3 ein zustimmungspflichtiges Geschäft und erfordert nach Paragraph 9 Abs. 2 Nr. 3 eine Mehrheit von 2/3 der Stimmen der anwesenden und vertretenen stimmberechtigten Kommanditisten. Mit 625.000 von 1.250.000 Stimmen (Paragraph 9 Abs. 4: je 1 EUR des Kapitalkontos eine Stimme) hält die Max Huber Rail GmbH genau 50 % und kann das Budget nicht einseitig bestimmen.

Auch eine gemeinschaftliche Führung nach IFRS 11 liegt nicht vor, weil für den Budgetbeschluss nicht die Zustimmung bestimmter, vertraglich festgelegter Parteien erforderlich ist, sondern unterschiedliche Gesellschafterkonstellationen die notwendige Mehrheit erreichen können.


TEILFRAGE 6 - Konsequenz für den Konzernabschluss

Da die Max Huber Rail GmbH die Paul Schwarz GmbH & Co. KG nicht beherrscht, ist diese nicht als Tochterunternehmen nach IFRS 10 in den Konzernabschluss einzubeziehen; eine Vollkonsolidierung scheidet aus. Da auch keine gemeinschaftliche Führung besteht, liegt keine gemeinsame Vereinbarung nach IFRS 11 vor; eine Bilanzierung als joint operation oder als joint venture kommt ebenfalls nicht in Betracht.

Die Max Huber Rail GmbH verfügt jedoch über maßgeblichen Einfluss im Sinne von IAS 28.3 in Verbindung mit IAS 28.5 und IAS 28.6. Dafür sprechen ihre 50 % der Stimmrechte, das Recht zur Benennung eines Geschäftsführers der Komplementärin (Paragraph 6 Abs. 8), das Letztentscheidungsrecht in operativen Angelegenheiten sowie die Möglichkeit, zustimmungspflichtige Geschäfte einschließlich der Budgetfestlegung zu blockieren. Die Beteiligung ist daher als assoziiertes Unternehmen einzustufen und nach IAS 28.16 nach der Equity-Methode zu bilanzieren, sofern keine Befreiung nach IAS 28.17 ff. eingreift.

Angabepflichten: Die Einschätzung, dass trotz eines Stimmrechtsanteils von 50 % und besonderer Entscheidungsrechte keine Beherrschung und keine gemeinschaftliche Führung vorliegt, ist eine wesentliche Ermessensentscheidung, die nach IFRS 12.7 in Verbindung mit IFRS 12.9 anzugeben und zu begründen ist. Hinzu treten die Angaben zu Anteilen an assoziierten Unternehmen nach IFRS 12.20 ff.

### Zugelassene Abweichungen (acceptable_variants)

Zu Teilfrage 1 (Maßgebliche Tätigkeiten): Eine weitergehende Aufzählung operativer maßgeblicher Tätigkeiten (Auftrags- und Projektakquise, Preis- und Kalkulationsentscheidungen, Personal- und Kapazitätssteuerung, Finanzierung) ist richtig, solange die Festlegung des Jahresbudgets als die ausschlaggebende Tätigkeit identifiziert wird. Statt 'Jahresbudget' sind 'Budgetfestlegung', 'Jahresplanung' oder 'Genehmigung der Unternehmensplanung' gleichwertig. Der zusätzliche Hinweis, dass die Festlegung des zustimmungspflichtigen Geschäftskatalogs selbst (Paragraph 6 Abs. 4) eine vorgelagerte Steuerungsebene bildet, ist zutreffend und nicht als Fehler zu werten.

Zu Teilfrage 2 (Besondere Entscheidungsrechte der Max Huber Rail GmbH): Die Einordnung der Rechte als substanzielle Rechte (substantive rights) im Sinne von IFRS 10.B22 ff., die aber nicht die maßgebliche Tätigkeit betreffen, ist gleichwertig zur obigen Formulierung. Ebenfalls zutreffend ist der Hinweis, dass das Vorschlagsrecht spiegelbildlich auch der Familie Schwarz zusteht und daher keine einseitige Position begründet, sowie der Hinweis, dass das Letztentscheidungsrecht bei einem Absinken der Beteiligung unter 50 % erlischt.

Zu Teilfrage 3 (Festlegung des Jahresbudgets): Die Angabe der Beteiligungsquote als 'genau 50 %', '625.000 von 1.250.000' oder '50 zu 50' ist gleichwertig. Der Hinweis, dass die Feststellung des Jahresabschlusses nach Paragraph 9 Abs. 2 Nr. 6 derselben 2/3-Mehrheit unterliegt, ist zutreffend. Wird Punkt 5 (Abstellen auf die anwesenden und vertretenen Stimmen, beschlussfähige zweite Versammlung) nicht erwähnt, ist die Antwort insoweit unvollständig, im Kern aber nicht falsch.

Zu Teilfrage 4 (Gemeinschaftliche Führung nach IFRS 11): Der Verweis auf IFRS 11.B5 bis B11 statt auf IFRS 11.7 ist gleichwertig. Die Begründung ist auch dann vollständig, wenn sie nur auf den Präsenzbezug der 2/3-Mehrheit abstellt und die beschlussfähige zweite Gesellschafterversammlung nicht gesondert erwähnt, solange das Argument der wechselnden Gesellschafterkonstellationen klar herausgearbeitet wird. Die zusätzliche Feststellung, dass mangels gemeinschaftlicher Führung auch keine Einordnung als joint operation oder joint venture in Betracht kommt, ist zutreffend.

Zu Teilfrage 5 (Ergebnis: Beherrschung nach IFRS 10): Zulässig sind Formulierungen wie 'niemand beherrscht', 'keiner der Gesellschafter beherrscht allein und es besteht auch keine gemeinschaftliche Führung' oder 'weder Beherrschung nach IFRS 10 noch joint control nach IFRS 11'. Die zusätzliche Feststellung, dass die Komplementärin AB Gleisbau GmbH trotz alleiniger Geschäftsführungsbefugnis nicht beherrscht, weil sie als Agent im Sinne von IFRS 10.B58 ff. handelt (keine Kapitaleinlage, kein Stimmrecht, keine Ergebnisbeteiligung), ist richtig und darf nicht als Fehler gewertet werden. Der Verweis auf 2/3 statt auf eine konkrete Prozentzahl ist gleichwertig.

Zu Teilfrage 6 (Konsequenz für den Konzernabschluss): Der Verweis auf die Equity-Methode ohne Nennung der konkreten Randnummer ist gleichwertig. Der Hinweis, dass die Einstufung als assoziiertes Unternehmen eine Ermessensentscheidung ist und alternativ - bei abweichender Würdigung des maßgeblichen Einflusses - eine Bilanzierung nach IFRS 9 in Betracht käme, ist als Nebenerwägung zulässig, sofern die Equity-Methode als das zutreffende Ergebnis benannt wird. Angaben zu Angabepflichten nach IFRS 12 sind verdienstvoll, aber nicht zwingend.

### Bewertungskriterien (grading_criteria)

Diese Aufgabe besteht aus sechs Teilfragen. Bewerten Sie JEDE Teilfrage einzeln von 0 bis 100 anhand der nachstehenden Kriterien und bilden Sie als score_percent den ungewichteten Durchschnitt der sechs Teilnoten. Eine nicht beantwortete oder nicht auffindbare Teilfrage ist mit 0 zu bewerten; sie darf nicht unbewertet bleiben und nicht aus dem Durchschnitt herausfallen. Bewerten Sie ausschließlich den fachlichen Gehalt: eine kurze, zutreffende Antwort auf eine Teilfrage ist voll zu werten, eine lange Antwort ohne den geforderten Inhalt nicht. Eine zutreffende Gesamtschlussfolgerung heilt keine fehlende oder falsche Teilantwort.

Wird in Teilfrage 5 eine andere Partei als beherrschend benannt oder in Teilfrage 4 eine gemeinschaftliche Führung bejaht, ist der Durchschnitt zusätzlich auf höchstens 50 Punkte zu begrenzen, weil die Aufgabe im Ergebnis verfehlt ist.

--- Kriterien Teilfrage 1 (Maßgebliche Tätigkeiten) ---
Answer must contain: (1) eine zutreffende Bestimmung der maßgeblichen Tätigkeiten als die renditewesentlichen operativen Tätigkeiten des Gleisbaugeschäfts (Ausschreibungen, ARGEn/Subunternehmerverhältnisse, Investitionen). (2) die Identifikation der Festlegung des Jahresbudgets als die ausschlaggebende maßgebliche Tätigkeit. (3) die Begründung, dass die operativen Entscheidungsrechte nach Paragraph 6 Abs. 8 nur innerhalb des Budgetrahmens ausgeübt werden können, mit Bezug auf die Formulierung 'innerhalb der bestehenden Budgetplanung'. (4) die Schlussfolgerung, dass die Beherrschungsfrage sich daran entscheidet, wer das Budget bestimmen kann.

Bewertung: Punkt (2) ist der Kern der Aufgabe. Eine Antwort, die maßgebliche Tätigkeiten nur allgemein beschreibt, das Budget aber nicht als ausschlaggebend erkennt, ist mit höchstens 35 Punkten zu bewerten, auch wenn sie im Uebrigen fachlich sauber ist. Werden (2) und (3) erfüllt, sind mindestens 70 Punkte zu vergeben. Der zusätzliche Verweis auf den verbindlichen Genehmigungsprozess der Anlage 1 (Paragraph 6 Abs. 5) ist verdienstvoll, aber nicht zwingend erforderlich.

--- Kriterien Teilfrage 2 (Besondere Entscheidungsrechte der Max Huber Rail GmbH) ---
Answer must contain: (1) die zutreffende Darstellung des Vorschlagsrechts für einen Geschäftsführer nach Paragraph 6 Abs. 8 einschließlich des Umstands, dass ein spiegelbildliches Recht der Familie Schwarz zusteht. (2) die Aufzählung der drei Angelegenheiten des Letztentscheidungsrechts (Ausschreibungen, ARGEn/Subunternehmerverhältnisse, Investitionsentscheidungen). (3) die entscheidende Feststellung, dass die Investitionsentscheidungen nur 'innerhalb der bestehenden Budgetplanung' getroffen werden können, die Rechte also budgetgebunden sind. (4) das Ergebnis, dass diese Rechte KEINE Verfügungsgewalt über die maßgeblichen Tätigkeiten im Sinne von IFRS 10.7(a) vermitteln. (5) die Begründung, dass die Festlegung des Budgets den Gesellschaftern vorbehalten ist und von der Max Huber Rail GmbH nicht allein herbeigeführt werden kann.

Bewertung: Punkt (3) in Verbindung mit (4) trägt die Aufgabe. Eine Antwort, die aus dem Letztentscheidungsrecht auf Beherrschung schließt, ist im Ergebnis falsch und mit höchstens 15 Punkten zu bewerten. Eine Antwort, die (4) richtig beantwortet, die Budgetgebundenheit nach (3) aber nicht erkennt, ist mit höchstens 45 Punkten zu bewerten. Die Einordnung der Rechte als bloße Schutzrechte (protective rights) ist fachlich unzutreffend und mit Abzug zu bewerten, führt aber nicht allein zu 0 Punkten.

--- Kriterien Teilfrage 3 (Festlegung des Jahresbudgets) ---
Answer must contain: (1) die Feststellung, dass die Festlegung des Jahresbudgets nach Anlage 3 Paragraph 3 Abs. 1 Nr. 3 ein zustimmungspflichtiges Geschäft ist. (2) die erforderliche Mehrheit von 2/3 der Stimmen der anwesenden und vertretenen stimmberechtigten Kommanditisten nach Paragraph 9 Abs. 2 Nr. 3. (3) die Stimmrechtsregel 'je 1 EUR des Kapitalkontos eine Stimme' nach Paragraph 9 Abs. 4 sowie den Ausschluss des Stimmrechts der Komplementärin nach Paragraph 9 Abs. 5. (4) die zutreffende Stimmverteilung: Max Huber Rail GmbH 625.000 von insgesamt 1.250.000 Stimmen, also genau 50 %, Familie Schwarz zusammen ebenfalls 50 %. (5) das Ergebnis, dass keine Partei die Budgetfestlegung allein herbeiführen kann.

Bewertung: Die Verknüpfung von (1) und (2) - also das Auffinden der Kette von der Anlage 3 in den Gesellschaftsvertrag - ist der eigentliche Prüfungsgegenstand. Fehlt diese Verknüpfung, sind höchstens 40 Punkte zu vergeben, auch wenn das Ergebnis (5) zutrifft. Rechenfehler bei der Quote (z. B. 'knapp über 50 %' statt 'genau 50 %') führen zu geringem Abzug, nicht zu 0 Punkten. Die zusätzlich richtige Darstellung des Präsenzbezugs der Mehrheit und der beschlussfähigen zweiten Gesellschafterversammlung nach Paragraph 8 Abs. 5 ist mit voller Punktzahl zu honorieren, aber für 100 Punkte nicht zwingend erforderlich.

--- Kriterien Teilfrage 4 (Gemeinschaftliche Führung nach IFRS 11) ---
Answer must contain: (1) das Ergebnis, dass KEINE gemeinschaftliche Führung vorliegt. (2) die zutreffende Wiedergabe des Maßstabs: gemeinschaftliche Führung erfordert, dass Entscheidungen über die maßgeblichen Tätigkeiten die einstimmige Zustimmung bestimmter, vertraglich festgelegter Parteien voraussetzen. (3) die tragende Begründung, dass hier keine solche feststehende Parteienkombination existiert, weil unterschiedliche Gesellschafterkonstellationen die erforderliche 2/3-Mehrheit erreichen können. (4) mindestens ein konkretes Beispiel einer solchen Konstellation, etwa Max Huber Rail GmbH gemeinsam mit einem Schwarz-Gesellschafter (rund 66,7 %) oder die Familie Schwarz in einer beschlussfähigen zweiten Gesellschafterversammlung.

Bewertung: Wird gemeinschaftliche Führung bejaht - etwa mit dem Argument, die 50/50-Verteilung führe zu wechselseitigen Vetorechten und damit zu joint control - ist die Antwort im Ergebnis falsch: höchstens 15 Punkte. Dieser Fehler ist die naheliegendste Fehleinschätzung des Falles und darf nicht mit Teilpunkten für eine ansonsten saubere IFRS-11-Darstellung ausgeglichen werden. Wird (1) richtig beantwortet, die Begründung (3) aber nicht auf die wechselnden Konstellationen gestützt, sind höchstens 50 Punkte zu vergeben. Volle Punktzahl nur bei (1) bis (3); (4) ist für mehr als 85 Punkte erforderlich.

--- Kriterien Teilfrage 5 (Ergebnis: Beherrschung nach IFRS 10) ---
Answer must contain: (1) das Ergebnis, dass KEINE Partei die Paul Schwarz GmbH & Co. KG beherrscht. (2) die ausdrückliche Verneinung der Alleinbeherrschung nach IFRS 10. (3) die ausdrückliche Verneinung der gemeinschaftlichen Führung nach IFRS 11. (4) als Begründung zumindest im Ansatz, dass die besonderen Entscheidungsrechte der Max Huber Rail GmbH nur innerhalb des Budgetrahmens bestehen und die Max Huber Rail GmbH das Budget nicht einseitig festlegen kann.

Bewertung: Wird als Ergebnis die Max Huber Rail GmbH, die Familie Schwarz, die Komplementärin oder irgendeine andere Partei als beherrschend genannt, ist die Antwort im Ergebnis falsch: höchstens 10 Punkte, unabhängig von der Qualität der Begründung. Wird nur die Alleinbeherrschung verneint, die gemeinschaftliche Führung aber nicht angesprochen oder sogar bejaht, sind höchstens 50 Punkte zu vergeben. Volle Punktzahl nur, wenn (1) bis (3) erfüllt sind und (4) wenigstens sinngemäß enthalten ist. Eine korrekte Schlussfolgerung ohne jede tragfähige Begründung ist mit höchstens 65 Punkten zu bewerten. Der Umfang der Antwort ist kein Bewertungskriterium; eine knappe, vollständige Antwort ist voll zu werten.

--- Kriterien Teilfrage 6 (Konsequenz für den Konzernabschluss) ---
Answer must contain: (1) die Feststellung, dass keine Vollkonsolidierung nach IFRS 10 erfolgt. (2) die Feststellung, dass mangels gemeinschaftlicher Führung auch keine Bilanzierung als gemeinsame Vereinbarung nach IFRS 11 in Betracht kommt. (3) die Bejahung eines maßgeblichen Einflusses und die Einstufung als assoziiertes Unternehmen nach IAS 28. (4) die Equity-Methode als anzuwendende Bilanzierungsmethode.

Bewertung: (1), (3) und (4) sind erforderlich. Fehlt (2), sind höchstens 75 Punkte zu vergeben. Wird eine Vollkonsolidierung oder eine Quotenkonsolidierung als Ergebnis genannt, ist die Antwort im Ergebnis falsch: höchstens 10 Punkte. Die Quotenkonsolidierung ist nach IFRS 11 ohnehin nicht mehr zulässig; ihre Nennung ist ein eigenständiger Fehler. Angaben zu IFRS 12 sind zusätzlich verdienstvoll und dürfen nicht als Abschweifung gewertet werden.


---
