# Milestone 3E Early-Game Runtime Checklist

All entries are draft text, prepared for controlled owner testing only. No new AzaharPlus runtime result is claimed. English and Russian are rendered segment-by-segment; control events are annotations that retain their original hexadecimal words. Source hashes identify the exact catalog variants used for the candidate build.

## Test procedure

Use disposable saves or begin a new game separately in Pokémon X and Pokémon Y with update 1.5 enabled. Do not overwrite an existing save. Check each visible line in the listed scene and report clipping, line breaks, substitutions, missing text, or incorrect branch selection. These candidates have not been installed.

### Coverage caveats

- The opening character-creation flow is not yet mapped to a text record. Do not treat the Pokédex Male/Female filter labels as protagonist selection.
- Exact event triggers for most newly translated messages are inferred from the message contents and archive organization. They need runtime confirmation.
- Protagonist correlation for branch records 2/3 is inferred from the named rival; verify it in each game and with both protagonist choices.
- Some extracted English source segments contain U+FFFD replacement characters. Those source decode issues are preserved as displayed and need investigation before final review.
- Owner-confirmed Milestone 3C runtime testing covered the earlier 12-record pilot in Pokémon X with a female protagonist (Options, mother, Calem, Shauna). Pokémon Y and Serena remain untested; that does not verify these new drafts.

## Language screen and Options

Verified scene note: the prior owner-tested 3C records were visible in the opening language-selection/Options flow in Pokémon X with a female protagonist. This milestone adds no runtime evidence.

### `a/0/7/4` · member `0075/0` · message `0`

- Source SHA-256: `6293a6436b72d9fb85a00150b6a75d9f00aa075f99cfc4295ebfbc3fbf6c28ef`
- Source versions: base, update-1.5
- Context: Options screen (trigger not runtime-verified unless stated above)
- State: `machine_draft`; human approval: pending
- English: OPTIONS
- Russian draft: НАСТРОЙКИ

### `a/0/7/4` · member `0075/0` · message `3`

- Source SHA-256: `ea76821fe1e96b22386a8523d06ea9a70e047806ba36bb4b2a93db9cc247b6a4`
- Source versions: base, update-1.5
- Context: Options screen (trigger not runtime-verified unless stated above)
- State: `machine_draft`; human approval: pending
- English: TEXT SPEED
- Russian draft: СКОРОСТЬ ТЕКСТА

### `a/0/7/4` · member `0075/0` · message `4`

- Source SHA-256: `4a8c1dac6f475f8d55e3d3a98d696aea2007bbde24614f4a91c85fd12f5c41f4`
- Source versions: base, update-1.5
- Context: Options screen (trigger not runtime-verified unless stated above)
- State: `machine_draft`; human approval: pending
- English: SLOW
- Russian draft: МЕДЛЕННО

### `a/0/7/4` · member `0075/0` · message `5`

- Source SHA-256: `f078935b274c76f143b64f0e0a51733ac64d99d5e140dfc8652e9b506bcb1c34`
- Source versions: base, update-1.5
- Context: Options screen (trigger not runtime-verified unless stated above)
- State: `machine_draft`; human approval: pending
- English: NORMAL
- Russian draft: НОРМАЛЬНО

### `a/0/7/4` · member `0075/0` · message `6`

- Source SHA-256: `ec7eb0e0e2fb8beb6e23d128ae0bd249572d441f8e4f42f5818b7e14df8715d1`
- Source versions: base, update-1.5
- Context: Options screen (trigger not runtime-verified unless stated above)
- State: `machine_draft`; human approval: pending
- English: FAST
- Russian draft: БЫСТРО

### `a/0/7/4` · member `0075/0` · message `7`

- Source SHA-256: `8b7a1facf5cbf9bad32dd1f4685b4c6335ca4d4fce44bb9f565c782f02273cd9`
- Source versions: base, update-1.5
- Context: Options screen (trigger not runtime-verified unless stated above)
- State: `machine_draft`; human approval: pending
- English: You can choose from three different text-scrolling speeds[LINE BREAK: 000A]to control how quickly messages appear.
- Russian draft: Выбери одну из трёх скоростей текста,[LINE BREAK: 000A]чтобы настроить темп показа сообщений.

## Character creation

No confirmed protagonist name/appearance prompt has been identified in the current English TextFile catalog. This is an unresolved scene/resource gap, not a zero-message translation claim.

## Vaniville Town and opening home dialogue

Scene location is inferred from the dialogue and resource context; only the earlier 3C pilot lines are owner-confirmed in X.

### `a/0/7/4` · member `0072/0` · message `6`

- Source SHA-256: `9d60b4af2098f3ea9218509f68224b6ce84eb016d18db75e5f4f70e7844de927`
- Source versions: base, update-1.5
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Vaniville Town
- Russian draft: Ванивайл-таун

### `a/0/7/4` · member `0072/0` · message `9`

- Source SHA-256: `e8c6c55a21514d8e146d0d6eb64b24379aed13295729f23188d50d791fa79496`
- Source versions: base, update-1.5
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Vaniville Pathway
- Russian draft: Тропа Ванивайл

### `a/0/7/4` · member `0072/0` · message `10`

- Source SHA-256: `fecf57276762b2ed3f74d3a20acd4b43053dc21c26334162eb741c7e068e79d4`
- Source versions: base, update-1.5
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Aquacorde Town
- Russian draft: Аквакорд-таун

### `a/0/8/2` · member `0055/0` · message `0`

- Source SHA-256: `6c00517edba1ad6d460b56713895ee737c670913ea9239e1b2af253ea37af19d`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: It’s a Wii U![LINE BREAK: 000A]The GamePad even has a screen!
- Russian draft: Это Wii U![LINE BREAK: 000A]Даже на геймпаде есть экран!

### `a/0/8/2` · member `0055/0` · message `1`

- Source SHA-256: `7785bd5dab9394c2e6acc68ef09bc76d3855d357baa7b026f69fbde87fcbd626`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000] checked the PC h[CONTROL: 0010 0003 1100 00FF 0202]iser dad gave h[CONTROL: 0010 0003 1100 00FF 0202]imer.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Adventure Rule No. 1[LINE BREAK: 000A]The X Button opens the menu![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Adventure Rule No. 2[LINE BREAK: 000A]Record your progress with SAVE.
- Russian draft: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]Ты проверил(а) компьютер, который [CONTROL: 0010 0003 1100 00FF 0202]папа подарил [CONTROL: 0010 0003 1100 00FF 0202]тебе.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Правило приключения № 1[LINE BREAK: 000A]Кнопка X открывает меню![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Правило приключения № 2[LINE BREAK: 000A]Сохраняй прогресс командой «СОХРАНИТЬ».

### `a/0/8/2` · member `0055/0` · message `2`

- Source SHA-256: `9424f425ae6232a169720ab239ccca3b06788ff1df1513e000e43441a2b563e0`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000] looked in the mirror...
- Russian draft: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000] посмотрел(а) в зеркало...

### `a/0/8/2` · member `0055/0` · message `3`

- Source SHA-256: `d75ef8c12f76833f88ecf762c7aa57a59ad4bce36d906b257a317fee7d51b3a5`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: ...And changed out of h[CONTROL: 0010 0003 1100 00FF 0202]iser pajamas!
- Russian draft: …И ты[CONTROL: 0010 0003 1100 00FF 0202]уже без пижамы!

### `a/0/8/2` · member `0055/0` · message `10`

- Source SHA-256: `fddaf7f91df2a738186cbb3611fd4e515bc75ea8f31db12478d59ef4d67c2764`
- Source versions: base
- Context: early-game dialogue (trigger not runtime-verified unless stated above)
- State: `machine_draft`; human approval: pending
- English: Morning, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]You sure slept well![LINE BREAK: 000A]All rested up from the move?
- Russian draft: Доброе утро, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Хорошо спалось?[LINE BREAK: 000A]Удалось отдохнуть после переезда?

### `a/0/8/2` · member `0055/0` · message `11`

- Source SHA-256: `0af408e578ef2d039e183f5b5a2477a110e8a327c270ce23218ce904905587a1`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![LINE BREAK: 000A]You look like you just rolled out of bed![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Go have a look at yourself in the mirror,[LINE BREAK: 000A]and change out of your pajamas.
- Russian draft: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![LINE BREAK: 000A]Похоже, ты только что встал(а) с постели![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Посмотри в зеркало,[LINE BREAK: 000A]и переоденься из пижамы.

### `a/0/8/2` · member `0055/0` · message `12`

- Source SHA-256: `8ef7211aa09ce1d0c2762e9a8864bcc0fc55fd0775803f7669f99dd31f60af34`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Go have a look at yourself in the mirror,[LINE BREAK: 000A]and change out of your pajamas.
- Russian draft: Посмотри в зеркало,[LINE BREAK: 000A]и переоденься из пижамы.

### `a/0/8/2` · member `0055/0` · message `13`

- Source SHA-256: `51b86af25101d1b8eee2e42315217ceccedbc2a10d9ad242cc77b450d08f01e0`
- Source versions: base
- Context: early-game dialogue (trigger not runtime-verified unless stated above)
- State: `machine_draft`; human approval: pending
- English: It’s about time you got going![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Why don’t you step out and say hello to[LINE BREAK: 000A]the neighbors?
- Russian draft: Пора тебе собираться![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Почему бы тебе не выйти и не поздороваться[LINE BREAK: 000A]с соседями?

### `a/0/8/2` · member `0055/0` · message `14`

- Source SHA-256: `a71df827b7637d1cd1e7f95bf943b89be31ea224986073b3ad41f0adac52034b`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Don’t wake up Rhyhorn, OK?
- Russian draft: Не разбуди Райхорна, ладно?

### `a/0/8/2` · member `0055/0` · message `15`

- Source SHA-256: `85accd672302f61f4dc8e7136dd41e6efd4d1f04892c3abafb419d024c61a169`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Really? The neighbor kids invited[LINE BREAK: 000A]you to the next town?[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]That’s great! I’m glad you were[LINE BREAK: 000A]able to make friends so quickly![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]OK! Have fun![LINE BREAK: 000A]Stay out of trouble!
- Russian draft: Правда? Соседские ребята пригласили[LINE BREAK: 000A]тебя в соседний город?[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Здорово! Как хорошо, что у тебя[LINE BREAK: 000A]так быстро появились друзья![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Ладно! Веселись![LINE BREAK: 000A]И не попадай в неприятности!

### `a/0/8/2` · member `0055/0` · message `16`

- Source SHA-256: `fc1e93661e1c31c15a395e24c1a041cd1b2b539843ba252208cf62b17e4614dc`
- Source versions: base
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Cheerp cheerp! ♪
- Russian draft: Чирик-чирик! ♪

### `a/0/8/2` · member `0055/0` · message `17`

- Source SHA-256: `a886ca00f6e0d0e282b6c44b521271afa6823c6f21d3214b16384375a95718b0`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: So! What did you and the neighbor kids[LINE BREAK: 000A]end up doing?
- Russian draft: Ну! Чем вы с соседскими ребятами[LINE BREAK: 000A]занимались?

### `a/0/8/2` · member `0055/0` · message `18`

- Source SHA-256: `edfb4146bb617c585dc563aae264e6f97ec17cf84e0abfbb81077d4be8ab0c04`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Wait one second, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![LINE BREAK: 000A]Is that a Poké Ball you have there?[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]You got your very own Pokémon?[LINE BREAK: 000A]Lucky you![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]How about that? You’re a Pokémon[LINE BREAK: 000A]Trainer now, too! Congratulations!
- Russian draft: Постой, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![LINE BREAK: 000A]Это у тебя Покебол?[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]У тебя теперь есть свой Покемон?[LINE BREAK: 000A]Вот здорово![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Теперь ты тоже тренер покемонов![LINE BREAK: 000A]Поздравляю!

### `a/0/8/2` · member `0055/0` · message `19`

- Source SHA-256: `c3629ba4f8515380229b9b219c6c41243601584fad2359c04d8b5f9a1b7c1564`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Huh?[LINE BREAK: 000A]A letter for me?[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]It says it’s from somebody named Sycamore.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]What could it be? A love letter?
- Russian draft: А?[LINE BREAK: 000A]Письмо для меня?[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Оно от некоего Сикамора.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Что же там? Любовное письмо?

### `a/0/8/2` · member `0055/0` · message `20`

- Source SHA-256: `1a5c1d03de0f8541e0e303c8f8f90b6ee62284c63bf158136f7fe346b7848d5c`
- Source versions: base
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: ... ... ...
- Russian draft: … … …

### `a/0/8/2` · member `0055/0` · message `21`

- Source SHA-256: `8e004c244cc96974252d1b0c72b943a3793e67d720f513e46113f95ea0a2b692`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Wow, what lovely handwriting...[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Hmm? What do we have here?[LINE BREAK: 000A]A request...[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Oh, I see!
- Russian draft: Вот это почерк...[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Хм? Что тут?[LINE BREAK: 000A]Просьба...[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]А, понятно!

### `a/0/8/2` · member `0055/0` · message `22`

- Source SHA-256: `e45a697fcca4893699b0ae7ca13323ffed0178e429489e92a7581e02d4d6b484`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]We’ve barely unpacked, and all kinds[LINE BREAK: 000A]of exciting things are happening![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]OK! Let’s get you and [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0001] ready for[LINE BREAK: 000A]your journey!
- Russian draft: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Мы ещё толком не распаковали вещи,[LINE BREAK: 000A]а уже столько всего происходит![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Ладно! Подготовим тебя и [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0001]к путешествию —[LINE BREAK: 000A]пора собираться!

### `a/0/8/2` · member `0055/0` · message `23`

- Source SHA-256: `cdb23212d8ab97fccb7e54dfc3c1319ff60e753d2d8cecc4f1b128bf4421eded`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Here you are, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000].[LINE BREAK: 000A]I even packed a change of clothes.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]My, what an unexpected turn of events![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]It’s just like a sudden last burst of speed from a[LINE BREAK: 000A]racer in a Rhyhorn race![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]You made friends![LINE BREAK: 000A]You met your Pokémon![CONTROL: 0010 0001 BE00][LINE BREAK: 000A]And now you get to take a lap around Kalos!
- Russian draft: Вот, держи, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000].[LINE BREAK: 000A]Я положила тебе сменную одежду.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Ну и неожиданный поворот![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Прямо как последний рывок[LINE BREAK: 000A]на гонках райхорнов![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]У тебя появились друзья![LINE BREAK: 000A]В твоей команде появился покемон![CONTROL: 0010 0001 BE00][LINE BREAK: 000A]Теперь ты отправишься в путешествие по Калосу!

### `a/0/8/2` · member `0055/0` · message `24`

- Source SHA-256: `3c3583ca954d36d9ca493709c9c1c29309cbf4da39d7df7a0db06cfb3ea3789a`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Oh, and don’t forget this!
- Russian draft: О, и вот ещё!

### `a/0/8/2` · member `0055/0` · message `25`

- Source SHA-256: `84e9724386726efb6a6aa1dc49650e26e009f9dceaa07bf449c7eb8c5de00292`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: You know how to use a Town Map, right?
- Russian draft: Ты знаешь, как пользоваться картой города?

### `a/0/8/2` · member `0055/0` · message `26`

- Source SHA-256: `46cb423e6f223de50b9ca033f0c43bd4730a5ffbf6307a221ce41d73a3cef76b`
- Source versions: base
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: That’s my [CONTROL: 0010 0003 1100 00FF 0403]boygirl![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Select the Town Map from your[LINE BREAK: 000A]Bag whenever you want to use it!
- Russian draft: Вот ты у меня [CONTROL: 0010 0003 1100 00FF 0403]молодец![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Карту города можно выбрать в сумке[LINE BREAK: 000A]когда она понадобится.

### `a/0/8/2` · member `0055/0` · message `27`

- Source SHA-256: `fa6ca225c6bac2366a5ba47620c70a320862075c62ad0c347ad6757565960166`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Press the X Button to open the Bag.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Next, use the +Control Pad to select[LINE BREAK: 000A]the KEY ITEMS Pocket.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Select the Town Map, and doing a lap[LINE BREAK: 000A]around the Kalos region will be a snap!
- Russian draft: Нажми X, чтобы открыть сумку.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Затем нажми + на крестовине и выбери[LINE BREAK: 000A]карман КЛЮЧЕВЫЕ ПРЕДМЕТЫ.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Выбери карту города — и путешествовать[LINE BREAK: 000A]по Калосу станет проще простого!

### `a/0/8/2` · member `0055/0` · message `28`

- Source SHA-256: `0c2afb502a0e43c7728805968c81a48ad3aa7ff7a8d6cdbb769641c23eaa77d8`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: I don’t know what this Professor Sycamore[LINE BREAK: 000A]wants you to see on your trip...[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]But taking a journey with your Pokémon[LINE BREAK: 000A]is a really wonderful experience.
- Russian draft: Не знаю, что профессор Сикамор[LINE BREAK: 000A]хочет показать тебе в путешествии...[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Но странствовать вместе со своим покемоном[LINE BREAK: 000A]— прекрасный опыт.

### `a/0/8/2` · member `0057/0` · message `1`

- Source SHA-256: `3367c3a3e45db586da5badb0f56a268ac986a0159ddea301a0336fed955f7d7f`
- Source versions: base
- Context: early-game dialogue (trigger not runtime-verified unless stated above)
- State: `machine_draft`; human approval: pending
- English: Welcome to Vaniville Town![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]My name’s Serena.[LINE BREAK: 000A]I’m your neighbor.
- Russian draft: Добро пожаловать в Ванивилл![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Меня зовут Серена.[LINE BREAK: 000A]Я твоя соседка.

### `a/0/8/2` · member `0057/0` · message `2`

- Source SHA-256: `4628f24796feeaa3d02f4b8f4cc5df66ac15f4c02698eebbd625c878bea967e7`
- Source versions: base
- Context: early-game dialogue (trigger not runtime-verified unless stated above)
- State: `machine_draft`; human approval: pending
- English: Welcome to Vaniville Town![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]The name’s Calem.[LINE BREAK: 000A]I live next door.
- Russian draft: Добро пожаловать в Ванивилл![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Меня зовут Калем.[LINE BREAK: 000A]Я живу по соседству.

### `a/0/8/2` · member `0057/0` · message `3`

- Source SHA-256: `ac64daefbdec046bef6685677f75ad19443f136d9fd6eac55b00fa322717f76f`
- Source versions: base
- Context: early-game dialogue (trigger not runtime-verified unless stated above)
- State: `machine_draft`; human approval: pending
- English: And I’m Shauna![LINE BREAK: 000A]Great to meet you![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Guess what![LINE BREAK: 000A]We’ve come to get you!
- Russian draft: А я Шауна![LINE BREAK: 000A]Приятно познакомиться![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]А знаешь что?[LINE BREAK: 000A]Мы пришли за тобой!

### `a/0/8/2` · member `0057/0` · message `4`

- Source SHA-256: `ea39b16d02ab9dfb780e1824eb7d0b43a3d3694ffbc68287c592caba233ebdcb`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The esteemed Professor Sycamore[LINE BREAK: 000A]lives here in the Kalos region.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]I was told he has a request for five kids,[LINE BREAK: 000A]including us.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]But I’m a little surprised he knows who you are.[LINE BREAK: 000A]You did just move to Vaniville, after all.
- Russian draft: Прославленный профессор Сикамор[LINE BREAK: 000A]живёт здесь, в Калосе.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Я слышала, что он позвал пятерых ребят,[LINE BREAK: 000A]включая нас.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Но я удивлена, что он знает, кто ты.[LINE BREAK: 000A]Ты ведь только недавно переехал в Ванивайл.

### `a/0/8/2` · member `0057/0` · message `5`

- Source SHA-256: `48dbfa66c4c89081a6c6195cd9bf428479297432ab27f4eb5824c50f39fb032b`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The renowned Professor Sycamore[LINE BREAK: 000A]lives here in the Kalos region.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]I heard he has a task for five kids, including us.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]But I’m surprised he knows who you are.[LINE BREAK: 000A]You did just move to Vaniville, after all.
- Russian draft: Известный профессор Сикамор[LINE BREAK: 000A]живёт здесь, в Калосе.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Я слышал, он позвал пятерых ребят, включая нас.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Но я удивлён, что он знает, кто ты.[LINE BREAK: 000A]Ты ведь только недавно переехала в Ванивайл.

### `a/0/8/2` · member `0057/0` · message `6`

- Source SHA-256: `b46c0c6799c0f203d9b7dd01e1369a32f852e1b7dcec26521b38ec44690b491a`
- Source versions: base
- Context: early-game dialogue (trigger not runtime-verified unless stated above)
- State: `machine_draft`; human approval: pending
- English: We’ll wait for you in the next town over![LINE BREAK: 000A]And you know what?![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]We’re going to get...a Pokémon![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]C’mon! Hurry! Let’s go!
- Russian draft: Будем ждать тебя в соседнем городе![LINE BREAK: 000A]И знаешь что?![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Скоро у нас будет… покемон![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Ну же, скорее! Пойдём!

### `a/0/8/2` · member `0057/0` · message `7`

- Source SHA-256: `876add0f79e638a7f86ca4df5dbbf15916e11e907ced4b6da48c135507e78ef7`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Grr... Groo...
- Russian draft: Грр... Грру...

### `a/0/8/2` · member `0057/0` · message `8`

- Source SHA-256: `d45c0157948e92ed6ff242c5699430cf96c0bf95051644ef18c8e73f3aa097a4`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Roaaaah!
- Russian draft: Р-р-а-а!

### `a/0/8/2` · member `0057/0` · message `9`

- Source SHA-256: `f21d2cbd6739f5a47b480766735fed3888a705e726e89284c5c201b8385be430`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: What was that just now?
- Russian draft: Что это сейчас было?

### `a/0/8/2` · member `0057/0` · message `10`

- Source SHA-256: `21411d85d1e18b098001ad32e041670004e267731b286487eea090f3318ed9e8`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Ha ha ha! What a card![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]I guess Rhyhorn just wanted to give you a big[LINE BREAK: 000A]send-off for your journey![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Well, it has known you since you were born,[LINE BREAK: 000A]after all!
- Russian draft: Ха-ха-ха! Вот проказник![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Наверное, Райхорн решил[LINE BREAK: 000A]громко проводить тебя в путь![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Ведь он знает тебя с самого рождения,[LINE BREAK: 000A]как-никак!

### `a/0/8/2` · member `0057/0` · message `11`

- Source SHA-256: `c9e6d7f7db8a0d0697b62401b67ad462146da44e3eecb844839afa9a70f9d9c1`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Good luck, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Go for broke![LINE BREAK: 000A]And don’t worry![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]You’ll have Pokémon by your side, so you’ll[LINE BREAK: 000A]be fine!
- Russian draft: Удачи, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Действуй на полную![LINE BREAK: 000A]И не волнуйся![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Покемоны будут рядом, так что[LINE BREAK: 000A]всё получится!

### `a/0/8/2` · member `0057/0` · message `12`

- Source SHA-256: `b92972a6e86c4a9543ff477bd51d3774091451d7abe9a1902452e24777044e3c`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: All right, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![LINE BREAK: 000A]Have fun on your journey with [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0001]![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Tell me all about the things[LINE BREAK: 000A]you experience in your travels!
- Russian draft: Ладно, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![LINE BREAK: 000A]Счастливого пути вместе с [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0001]![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Расскажи мне обо всём,[LINE BREAK: 000A]что увидишь в дороге!

### `a/0/8/2` · member `0057/0` · message `13`

- Source SHA-256: `0cc620c897f76b4f723e0e86c4df6922953cf985573f6141027fe74e4c4228b0`
- Source versions: base
- Context: opening home/neighbor dialogue (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Vaniville Town is pretty nice, right?[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]The Kalos region has lots of cool towns![LINE BREAK: 000A]I want to see them all when I get big!
- Russian draft: Ванивайл — хороший городок, правда?[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]В Калосе столько замечательных городов![LINE BREAK: 000A]Когда вырасту, хочу побывать в каждом!

## Protagonist-specific branches

### `a/0/8/2` · member `0053/0` · message `0`

- Source SHA-256: `e4c27686967c55a74e1b3b9fdeb472ecf1d333a61d83c796253b282bbe13c33c`
- Source versions: base
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Oh, you must be the new young man from[LINE BREAK: 000A]next door. Welcome to Vaniville Town![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]We have a daughter who is just about the[LINE BREAK: 000A]same age as you. If you meet our Serena,[CONTROL: 0010 0001 BE00][LINE BREAK: 000A]I hope you two will become good friends.
- Russian draft: О, ты, должно быть, новый мальчик из[LINE BREAK: 000A]соседнего дома. Добро пожаловать в Ванивайл![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]У нас есть дочь примерно твоего[LINE BREAK: 000A]возраста. Если встретишь Серену,[CONTROL: 0010 0001 BE00][LINE BREAK: 000A]надеюсь, вы станете хорошими друзьями.

### `a/0/8/2` · member `0053/0` · message `1`

- Source SHA-256: `b08a8349032dd8fe0d951a3848cdceda14342fe249a2c75b4c53d6731fd05f78`
- Source versions: base
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Oh, you must be the new young lady from[LINE BREAK: 000A]next door. Welcome to Vaniville Town![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]We have a son who is just about the same[LINE BREAK: 000A]age as you. If you do meet our Calem,[CONTROL: 0010 0001 BE00][LINE BREAK: 000A]I hope you two will become good friends.
- Russian draft: О, ты, должно быть, новая девочка из[LINE BREAK: 000A]соседнего дома. Добро пожаловать в Ванивайл![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]У нас есть сын примерно твоего[LINE BREAK: 000A]возраста. Если встретишь Калема,[CONTROL: 0010 0001 BE00][LINE BREAK: 000A]надеюсь, вы станете хорошими друзьями.

### `a/0/8/2` · member `0053/0` · message `2`

- Source SHA-256: `30363975352334fd574ab7c835c2fa91f8c11aae938e113e5d6994272a018f7a`
- Source versions: base
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Hmm! I like the look on your Pokémon’s face.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]I bet that if you and my Serena battled each[LINE BREAK: 000A]other, you’d both grow from the experience!
- Russian draft: Хм! Мне нравится выражение мордочки твоего покемона.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Уверен, если бы ты сразился с Сереной,[LINE BREAK: 000A]этот бой помог бы вам обоим стать сильнее!

### `a/0/8/2` · member `0053/0` · message `3`

- Source SHA-256: `7b0d7aee3247d67f7697eaaaaee61d79da546225a388d56a0b086e1ce5eddf20`
- Source versions: base
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Hmm! I like the look on your Pokémon’s face.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]I bet that if you and my Calem battled each[LINE BREAK: 000A]other, you’d both grow from the experience!
- Russian draft: Хм! Мне нравится выражение мордочки твоего покемона.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Уверен, если бы ты сразилась с Калемом,[LINE BREAK: 000A]этот бой помог бы вам обоим стать сильнее!

## Aquacorde Town opening sequence

Message IDs 0–59 in this member form the extracted Aquacorde opening dialogue set. Individual trigger order and conditional selection are not runtime-verified.

### `a/0/8/2` · member `0049/0` · message `0`

- Source SHA-256: `1a418c94f2a25c6c9ea92ee11635ced59a9d63e6c072fbfb9133cb3173e8318e`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Hey, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![LINE BREAK: 000A]This way! Over here!
- Russian draft: Эй, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![LINE BREAK: 000A]Сюда! Иди сюда!

### `a/0/8/2` · member `0049/0` · message `1`

- Source SHA-256: `1a418c94f2a25c6c9ea92ee11635ced59a9d63e6c072fbfb9133cb3173e8318e`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Hey, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![LINE BREAK: 000A]This way! Over here!
- Russian draft: Эй, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]![LINE BREAK: 000A]Сюда! Иди сюда!

### `a/0/8/2` · member `0049/0` · message `2`

- Source SHA-256: `472863c7c054a826c52ca5fae0daa038912cb244dae3e39864cbcb0388ad8d99`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: We were just talking about you!
- Russian draft: Мы как раз о тебе говорили!

### `a/0/8/2` · member `0049/0` · message `3`

- Source SHA-256: `ea86d9a7f8a77f6a529c3cafbc44c41f53f5056070293ce8ea88e478f6d9372b`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: C’mon, have a seat!
- Russian draft: Садись с нами!

### `a/0/8/2` · member `0049/0` · message `4`

- Source SHA-256: `87415cef282abbb861a63d43335e41354e72aad622c27b8dc8d948fa3aa04ad5`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: This is the meeting place, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000].
- Russian draft: Это место встречи, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000].

### `a/0/8/2` · member `0049/0` · message `5`

- Source SHA-256: `c5bdb041b82226880670a7553b7d8765e750deccf33f6be7a5d8a64c09daaa6f`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Here, let me introduce you.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Everyone, this is [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000].
- Russian draft: Позволь представить тебя всем.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Знакомьтесь, это [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000].

### `a/0/8/2` · member `0049/0` · message `6`

- Source SHA-256: `87415cef282abbb861a63d43335e41354e72aad622c27b8dc8d948fa3aa04ad5`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: This is the meeting place, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000].
- Russian draft: Это место встречи, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000].

### `a/0/8/2` · member `0049/0` · message `7`

- Source SHA-256: `1a3a0c0f67abb6e1b877ff6b86a38ab2e10377c3c6e232050cd206f8f97b3256`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: I’ll introduce you.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Everyone, this is [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000].
- Russian draft: Я вас познакомлю.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Знакомьтесь, это [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000].

### `a/0/8/2` · member `0049/0` · message `8`

- Source SHA-256: `69c6a540df22d47168c0375c8ef84c08a37ba1ef151c4c2a76bb28687cfc005f`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Wow...[LINE BREAK: 000A]Shauna’s description was spot on!
- Russian draft: Вот...[LINE BREAK: 000A]Шауна описала тебя точь-в-точь!

### `a/0/8/2` · member `0049/0` · message `9`

- Source SHA-256: `a486a9424df56c250bd501ac5df96d57a3c77c1b5e4933f8cb025ab45d5636da`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: So, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000], this is Tierno.[LINE BREAK: 000A]He’s got some serious dance moves, and...
- Russian draft: Итак, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000], это Тиерно.[LINE BREAK: 000A]Он здорово танцует, и...

### `a/0/8/2` · member `0049/0` · message `10`

- Source SHA-256: `3ae8ed408ae9411e8f362efe469bf6cd37d189cbbce4186b765f5543de5f77dd`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: This is Trevor. He never misses a single[LINE BREAK: 000A]question on his tests, but he’s a little shy...
- Russian draft: А это Тревор. Он ни разу не ошибается в[LINE BREAK: 000A]ответах на тестах, но немного стесняется...

### `a/0/8/2` · member `0049/0` · message `11`

- Source SHA-256: `fc27d028c0eab50766b907096dd0248e52b851d65c14280b2406a95b3283b412`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: So, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]. This is Tierno.[LINE BREAK: 000A]He can really tear up the dance floor...
- Russian draft: Итак, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]. Это Тиерно.[LINE BREAK: 000A]Он зажигает на танцполе...

### `a/0/8/2` · member `0049/0` · message `12`

- Source SHA-256: `cddf964248d49463a7df8fb74553f68442fe4554b799d30dca9c9208d268d8fa`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: And this is Trevor. He’s a little shy, but he[LINE BREAK: 000A]always gets perfect scores on his tests...
- Russian draft: А это Тревор. Он немного стеснительный, но[LINE BREAK: 000A]в тестах всегда получает высшие баллы...

### `a/0/8/2` · member `0049/0` · message `13`

- Source SHA-256: `c38054e99583a3324871324cd3fecf7a071d389b2ec81261648fca5d2d997fd2`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: All right! Nice to meetcha![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]You know, it’d feel like we’re a closer crew[LINE BREAK: 000A]if we call each other by nicknames.[CONTROL: 0010 0001 BE00][LINE BREAK: 000A]Can I call you Lady [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 018A 0001]?
- Russian draft: Вот и познакомились![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Знаешь, прозвища помогут нам стать ближе.[LINE BREAK: 000A]Давай будем звать друг друга по прозвищам.[CONTROL: 0010 0001 BE00][LINE BREAK: 000A]Можно я буду звать тебя леди [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 018A 0001]?

### `a/0/8/2` · member `0049/0` · message `14`

- Source SHA-256: `60487164d0d1d8f1e3c41ddd6e762c7bae32a5fac588a1af86cddf8a916aca18`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: All right! Nice to meetcha![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]You know, it’d feel like we’re a closer crew[LINE BREAK: 000A]if we call each other by nicknames.[CONTROL: 0010 0001 BE00][LINE BREAK: 000A]Can I call you [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 018A 0001]-Meister?
- Russian draft: Вот и познакомились![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Знаешь, прозвища помогут нам стать ближе.[LINE BREAK: 000A]Давай будем звать друг друга по прозвищам.[CONTROL: 0010 0001 BE00][LINE BREAK: 000A]Можно я буду звать тебя мастером [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 018A 0001]?

### `a/0/8/2` · member `0049/0` · message `15`

- Source SHA-256: `da5e26031501879db8c49fd0750f64c714a350c3be66cbbe4ec7b0fd06c66caa`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: What? No way![LINE BREAK: 000A]She’s a Li’l [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 018A 0001], for sure!
- Russian draft: Что? Да ну![LINE BREAK: 000A]Она точно малышка [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 018A 0001]!

### `a/0/8/2` · member `0049/0` · message `16`

- Source SHA-256: `32095e30484c79f5e304924b39084d9c5693380c6c0f4c243ac915e6528078e8`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: What? No way![LINE BREAK: 000A]He’s a Li’l [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 018A 0001], for sure!
- Russian draft: Что? Да ну![LINE BREAK: 000A]Он точно малыш [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 018A 0001]!

### `a/0/8/2` · member `0049/0` · message `17`

- Source SHA-256: `0765559f2f582f5875111ef3001a506710da688f09a972c4f5b76f8c347e6482`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: What do you think, Trevor?
- Russian draft: Как думаешь, Тревор?

### `a/0/8/2` · member `0049/0` · message `18`

- Source SHA-256: `f3deb5e98441a9575c4c63448b563a1478b1e2bc8d2172041816c867c532e1c9`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: What?! You want me to nickname[LINE BREAK: 000A]someone I just met?![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Shauna, you shouldn’t put people[LINE BREAK: 000A]on the spot like this.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Well...how about something low key?[LINE BREAK: 000A]Maybe...something like [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 018A 0001]-kins?
- Russian draft: Что?! Ты хочешь, чтобы я дал прозвище[LINE BREAK: 000A]человеку, которого только что встретил?![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Шауна, не ставь людей в неловкое положение.[LINE BREAK: 000A]Это не очень-то вежливо.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Может... что-нибудь попроще?[LINE BREAK: 000A]Например, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 018A 0001]-кинс?

### `a/0/8/2` · member `0049/0` · message `19`

- Source SHA-256: `ff28a65982f64caec97d56fafc70eaace3037d77bc5fa84c0b1e48636ca4d542`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: What?! You want me to nickname[LINE BREAK: 000A]someone I just met?![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Shauna, you shouldn’t put people[LINE BREAK: 000A]on the spot like this.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Well...how about something low key?[LINE BREAK: 000A]Maybe...something like Big [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 018A 0001]...
- Russian draft: Что?! Ты хочешь, чтобы я дал прозвище[LINE BREAK: 000A]человеку, которого только что встретил?![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Шауна, не ставь людей в неловкое положение.[LINE BREAK: 000A]Это не очень-то вежливо.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Может... что-нибудь попроще?[LINE BREAK: 000A]Например, Большой [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 018A 0001]?

### `a/0/8/2` · member `0049/0` · message `20`

- Source SHA-256: `d20b80488cd2922436731b733c47826f9399cc8461217a879d1df68c02bf3bf2`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Why don’t you decide what we should call you?
- Russian draft: Реши сам, как нам тебя называть.

### `a/0/8/2` · member `0049/0` · message `21`

- Source SHA-256: `5c8c7bca393070fac77d5db63420aed742b0dce8212ba9de08d5267dd3705942`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: You should decide what we call you.
- Russian draft: Выбери себе прозвище сам.

### `a/0/8/2` · member `0049/0` · message `22`

- Source SHA-256: `e25907e4422c63660edd7307cadb91c51906bed67e184f21712925bbb62c33d1`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: You want us to call you [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002]?
- Russian draft: Хотите звать тебя [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002]?

### `a/0/8/2` · member `0049/0` · message `23`

- Source SHA-256: `0abff2fcb765f674a26f8237fa8fb7bb7210f428d08f2fdc19706ed5b58e0704`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: OK! ♪[LINE BREAK: 000A][VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002] fits you perfectly![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]I’m sure we’re gonna be great[LINE BREAK: 000A]friends, so I’ll call you that, too!
- Russian draft: Ладно! ♪[LINE BREAK: 000A][VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002] тебе отлично подходит![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Уверена, мы станем хорошими[LINE BREAK: 000A]друзьями, и я тоже буду так тебя звать!

### `a/0/8/2` · member `0049/0` · message `24`

- Source SHA-256: `a4ecf595c6ed3098de949218e838acfddd981380ee0a17a8ee7a2e0abf395431`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Hey! Can we see the Pokémon now?[LINE BREAK: 000A]I want to meet my new partner soon! ♪
- Russian draft: Эй! Можно уже посмотреть на покемонов?[LINE BREAK: 000A]Хочу скорее познакомиться со своим напарником! ♪

### `a/0/8/2` · member `0049/0` · message `25`

- Source SHA-256: `e5c9ea28d0d4e4e31511ea55ec33c349f0c5a7fbe02fbe0214e0e77a0069b6e1`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: I know, right? It was such a cool feeling[LINE BREAK: 000A]when Trevs and I met our Pokémon![CONTROL: 0010 0001 BE00][LINE BREAK: 000A]Hope you feel the same way we did!
- Russian draft: Ага! Когда мы с Тревсом встретили[LINE BREAK: 000A]своих покемонов, это было так здорово![CONTROL: 0010 0001 BE00][LINE BREAK: 000A]Надеюсь, ты тоже испытаешь это чувство!

### `a/0/8/2` · member `0049/0` · message `26`

- Source SHA-256: `245415eeaf900a30628c64ba24205fb850c0159e090752825a0c576b7dc93a25`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002], why don’t[LINE BREAK: 000A]you go ahead and pick first?
- Russian draft: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002], теперь твоя очередь[LINE BREAK: 000A]выбирать!

### `a/0/8/2` · member `0049/0` · message `27`

- Source SHA-256: `7cc3a0782c9ff50f1cfbbdf2502f160191d5e0b899ead46502a9274a62331d08`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002], you can pick first.
- Russian draft: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002], выбирай ты.

### `a/0/8/2` · member `0049/0` · message `28`

- Source SHA-256: `2d3b3cdbd7366c5b743075a890a87c96f4480df0ce7627f68a89500de4c916a7`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Hmmmmmm...[LINE BREAK: 000A]It’s so hard to decide!
- Russian draft: У-у-у...[LINE BREAK: 000A]Так трудно выбрать!

### `a/0/8/2` · member `0049/0` · message `29`

- Source SHA-256: `5d70d0c4f345e0a14b672a5c263c124aebafc7496166328343b127ced2387410`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: What? Seriously?[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Where are you going?[LINE BREAK: 000A]Let’s pick our Pokémon!
- Russian draft: Что? Серьёзно?[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Куда ты собрался?[LINE BREAK: 000A]Давай выбирать покемона!

### `a/0/8/2` · member `0049/0` · message `30`

- Source SHA-256: `e8b184ea3840159abdccac05d11b293139e75bc8829e45a1538baf8698a12a14`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Are you going to pick a Pokémon?
- Russian draft: Будешь выбирать покемона?

### `a/0/8/2` · member `0049/0` · message `31`

- Source SHA-256: `70fcdb46db63401c82e91f577f2803cb512b7429260560eb51c2bd9d7e8d7b7d`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Here you are, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002]![LINE BREAK: 000A]Which one will be your partner?
- Russian draft: Вот, держи, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002]![LINE BREAK: 000A]Кто станет твоим напарником?

### `a/0/8/2` · member `0049/0` · message `32`

- Source SHA-256: `cda44c9556c769644ddc9d770e18fe5a99a27321896c47d1896bfeacffc29681`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: OK! It’s a big decision.[LINE BREAK: 000A]Take some time to think about it.
- Russian draft: Да, решение важное.[LINE BREAK: 000A]Не торопись, подумай.

### `a/0/8/2` · member `0049/0` · message `33`

- Source SHA-256: `63d32cade037b422de766337dc95c41327f5ec06a365e32998deb1adb63ba858`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The two of us have already picked our partners.[LINE BREAK: 000A]Pokémon truly are amazing, aren’t they?
- Russian draft: Мы уже выбрали себе напарников.[LINE BREAK: 000A]Покемоны и правда удивительные, да?

### `a/0/8/2` · member `0049/0` · message `34`

- Source SHA-256: `3df5b5b7e4454c66bd64687aecbf5cf2dd92290fa1e8553c1bea12f9476e851b`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Would you like to give your[LINE BREAK: 000A]Pokémon a nickname?
- Russian draft: Хочешь дать своему[LINE BREAK: 000A]покемону прозвище?

### `a/0/8/2` · member `0049/0` · message `35`

- Source SHA-256: `0c4e4a38dd947df82e020252b843dd0c8d4c71fe235b32452c444d738baa88a9`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: So, you’ve decided on the[LINE BREAK: 000A]nickname [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0102 0005]?
- Russian draft: Ты выбрал прозвище[LINE BREAK: 000A]«[VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0102 0005]»?

### `a/0/8/2` · member `0049/0` · message `36`

- Source SHA-256: `5e064c479e6030ba38b3755a99831b85158a5ae1e1926b6db6bc87ace4ba0bcb`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: So, you’re not going to give[LINE BREAK: 000A]your Pokémon a nickname? ♪
- Russian draft: Значит, прозвище своему[LINE BREAK: 000A]покемону давать не будешь? ♪

### `a/0/8/2` · member `0049/0` · message `37`

- Source SHA-256: `cc7ce30ff1dbbc51f7d95e4003c44f74d289fc98e97901a30c24243f0dc8a8c3`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: OK! My partner is [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0003]![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Wow! We go together great![LINE BREAK: 000A]The two of us are just way-ay-ay too cute! ♪
- Russian draft: Мой напарник — [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0003]![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Вот мы и нашли друг друга![LINE BREAK: 000A]Мы с ним просто очаровашки! ♪

### `a/0/8/2` · member `0049/0` · message `38`

- Source SHA-256: `cec7cba4fa9a7950f4c27f7d3fee8b73637cbe0d7c31dfa7c531180141a06add`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Nice to meet you, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0004].[LINE BREAK: 000A]I’m Serena.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Because of you, I can be a real[LINE BREAK: 000A]Pokémon Trainer. Thank you!
- Russian draft: Приятно познакомиться, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0004].[LINE BREAK: 000A]Я Серена.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Благодаря тебе я стала настоящим[LINE BREAK: 000A]тренером покемонов. Спасибо!

### `a/0/8/2` · member `0049/0` · message `39`

- Source SHA-256: `860c2545e7d1d34a4c6ea49f50d8f580c3f9a60a1f99279ece00c91fb795ccfb`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Good to meet you, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0004].[LINE BREAK: 000A]My name’s Calem.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Because of you, I can be a real[LINE BREAK: 000A]Pokémon Trainer. Thanks!
- Russian draft: Рад знакомству, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0004].[LINE BREAK: 000A]Я Калем.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Благодаря тебе я стал настоящим[LINE BREAK: 000A]тренером покемонов. Спасибо!

### `a/0/8/2` · member `0049/0` · message `40`

- Source SHA-256: `f3ac84458d8cb573ed7ee7817027bf4920af37f1e1baff6484014e70b95bcfdc`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Uh, pardon me, but I have something[LINE BREAK: 000A]for you from the professor as well.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]I have something that will help you understand[LINE BREAK: 000A]Pokémon on a much deeper level.
- Russian draft: Простите, у меня тоже есть[LINE BREAK: 000A]кое-что для тебя от профессора.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Это поможет тебе лучше понять[LINE BREAK: 000A]покемонов.

### `a/0/8/2` · member `0049/0` · message `41`

- Source SHA-256: `f37439803bab17b81bf916ba7b82ce4801e36272defcb32973bfa8b814903960`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000] received[LINE BREAK: 000A]a [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 FF00 0002]Pokédex[VARIABLE / PLACEHOLDER CONTROL: 0010 0002 FF00 0000]!
- Russian draft: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000] получает[LINE BREAK: 000A]свой [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 FF00 0002]Покедекс[VARIABLE / PLACEHOLDER CONTROL: 0010 0002 FF00 0000]!

### `a/0/8/2` · member `0049/0` · message `42`

- Source SHA-256: `24ff2f66e79a551ec7b36b35fe2b980d6e773f8d54cf793af41e796f2dd3956e`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Um, so you see...[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]The Pokédex I just gave you is[LINE BREAK: 000A]a high-tech device that automatically[CONTROL: 0010 0001 BE00][LINE BREAK: 000A]records the Pokémon you encounter![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]The reason you get one is because[LINE BREAK: 000A]the professor wants us to go on[CONTROL: 0010 0001 BE00][LINE BREAK: 000A]a journey with our Pokémon[CONTROL: 0010 0001 BE00][LINE BREAK: 000A]and complete the Pokédex.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]To put it another way, it’s an important[LINE BREAK: 000A]mission from the professor. I’m sure of it!
- Russian draft: Ну, понимаешь...[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Покедекс, который я тебе дал, —[LINE BREAK: 000A]высокотехнологичный прибор, который[CONTROL: 0010 0001 BE00][LINE BREAK: 000A]автоматически записывает[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]встреченных тобой покемонов![LINE BREAK: 000A]Профессор выдал нам его,[CONTROL: 0010 0001 BE00][LINE BREAK: 000A]потому что хочет, чтобы мы[CONTROL: 0010 0001 BE00][LINE BREAK: 000A]отправились в путешествие[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]и заполнили Покедекс.[LINE BREAK: 000A]Это важное поручение профессора, я уверен!

### `a/0/8/2` · member `0049/0` · message `43`

- Source SHA-256: `2329aa6c143566074d40e630627ae07de33e21713a45b96a73fd2ef21b23175d`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Oh lighten up, Trevs![LINE BREAK: 000A]You’re way too serious sometimes.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Um, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002]...[LINE BREAK: 000A]Please take this with you, too.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]It’s a letter from the professor.[LINE BREAK: 000A]He said you should give it to your mom.
- Russian draft: Да не переживай, Тревс![LINE BREAK: 000A]Ты иногда слишком серьёзен.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Эй, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002]...[LINE BREAK: 000A]Возьми ещё вот это.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Это письмо от профессора.[LINE BREAK: 000A]Он просил передать его твоей маме.

### `a/0/8/2` · member `0049/0` · message `44`

- Source SHA-256: `215fd82beda753e0d17d7371fe22a0c3bd00e91aa05c0186d66f231b26ee60ac`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: All right! We’re done with our[LINE BREAK: 000A]errand for the professor.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]I guess Trevs and I will[LINE BREAK: 000A]go look for Pokémon![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Let’s go, Trevs!
- Russian draft: Вот и всё! Мы выполнили[LINE BREAK: 000A]поручение профессора.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Пойдём, Тревс,[LINE BREAK: 000A]искать покемонов![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Пойдём!

### `a/0/8/2` · member `0049/0` · message `45`

- Source SHA-256: `2109246aff7f9a429cb798a2095991b394fa489ba970868673f648fad2666926`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: In Kalos, kids are chosen to carry a Pokédex[LINE BREAK: 000A]and go on an adventure.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]But you need to give that letter[LINE BREAK: 000A]to your mom before you go.
- Russian draft: В Калосе детям поручают взять Покедекс[LINE BREAK: 000A]и отправиться в путешествие.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Но сначала отнеси письмо[LINE BREAK: 000A]маме.

### `a/0/8/2` · member `0049/0` · message `46`

- Source SHA-256: `be1015fc788b163d0bee15d7a58c69b3f3075790b83849b3725bd47f48797894`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: In Kalos, kids are chosen to carry a Pokédex[LINE BREAK: 000A]and go on an adventure.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]But you need to give that letter[LINE BREAK: 000A]to your mom before any of that.
- Russian draft: В Калосе детям поручают взять Покедекс[LINE BREAK: 000A]и отправиться в путешествие.[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Но сначала отнеси письмо[LINE BREAK: 000A]маме.

### `a/0/8/2` · member `0049/0` · message `47`

- Source SHA-256: `7bb54914579a74d2cab44812cdc81125fb2ed3470f0411b1e40c209146cbdec5`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: If you have a Pokémon partner,[LINE BREAK: 000A]you have nothing to fear from wild Pokémon.
- Russian draft: С покемоном-напарником[LINE BREAK: 000A]дикие покемоны тебе не страшны.

### `a/0/8/2` · member `0049/0` · message `48`

- Source SHA-256: `d69d873a318c0491c8bba477df195d716f9338df6e0e39d0794d08763fc20078`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: If you have a Pokémon partner,[LINE BREAK: 000A]you can battle wild Pokémon.
- Russian draft: С покемоном-напарником[LINE BREAK: 000A]ты сможешь сражаться с дикими покемонами.

### `a/0/8/2` · member `0049/0` · message `49`

- Source SHA-256: `f1f327bf3866d4dcc86857fb332cd30253a10217305b8f0ff4deecf0e89b8b8e`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: My very own [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0003]![LINE BREAK: 000A]I want to play together soon![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]With a little one like this with me,[LINE BREAK: 000A]I’m sure my journey’ll be great! ♪
- Russian draft: У меня теперь есть свой [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0003]![LINE BREAK: 000A]Скоро мы будем играть вместе![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]С ним я отправлюсь в путешествие,[LINE BREAK: 000A]и оно будет замечательным! ♪

### `a/0/8/2` · member `0049/0` · message `50`

- Source SHA-256: `c32cb2bfc8ae46bbea8f097ca98eefdaf0c0a2b76bbc1bbd8c78d395f359d2e6`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002], wait!
- Russian draft: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002], подожди!

### `a/0/8/2` · member `0049/0` · message `51`

- Source SHA-256: `8b216ce307e29f05e826aa36bd3044d81448c426611f22f1e008c79c37750989`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: You’re gonna be my opponent in my[LINE BREAK: 000A]Pokémon-battling debut!
- Russian draft: Ты станешь моим первым[LINE BREAK: 000A]соперником в бою покемонов!

### `a/0/8/2` · member `0049/0` · message `52`

- Source SHA-256: `039cdf88ac5eeb98c408577ccd419e49874f21ffc3f10fb995cee8eee5dab1b2`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: OK, Li’l [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0003]![LINE BREAK: 000A]It’s our first battle![CONTROL: 0010 0001 BE00][LINE BREAK: 000A]Let’s win it with style!
- Russian draft: Ладно, малыш [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0003]![LINE BREAK: 000A]Это наш первый бой![CONTROL: 0010 0001 BE00][LINE BREAK: 000A]Давай победим красиво!

### `a/0/8/2` · member `0049/0` · message `53`

- Source SHA-256: `f7e9f1fe8f8e64da5b13a72c8d617d582856c4df04bd30d561c6d45184430793`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: You’re amazing, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002]![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Here! Let me fix up your Pokémon. ♪
- Russian draft: Ты отлично сражался, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002]![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Давай я подлечу твоих покемонов. ♪

### `a/0/8/2` · member `0049/0` · message `54`

- Source SHA-256: `3d0454c53ef62af39b282e4828f28599186fe294ef183866735a36beed9eff37`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Pretty good! Right, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002]?[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Here, let me fix up your Pokémon. ♪
- Russian draft: Неплохо! Ну как, [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0189 0002]?[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Давай я подлечу твоих покемонов. ♪

### `a/0/8/2` · member `0049/0` · message `55`

- Source SHA-256: `c9d418e6d2b832e82360e1707ef95dcec6f968ced1b54325bea84f3ded70091f`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Say hi to your mom for me! ♪
- Russian draft: Передавай маме привет! ♪

### `a/0/8/2` · member `0049/0` · message `56`

- Source SHA-256: `cfcdb8e2634430387316e1765b0a3b33349d6f479a7b3dd0aaecbfc38457d1bc`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Well, I guess I’d better go and[LINE BREAK: 000A]battle some wild Pokémon![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]I have to make my Pokémon[LINE BREAK: 000A]strong, after all! ♪
- Russian draft: Пожалуй, пойду[LINE BREAK: 000A]сражаться с дикими покемонами![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Надо сделать моего покемона[LINE BREAK: 000A]сильнее! ♪

### `a/0/8/2` · member `0049/0` · message `57`

- Source SHA-256: `7dd0c84c90f9c4324a601a8c6d6b7304596f85a7d2bb40f34b9366e1b572e66a`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Oh! So you’re one of the kids[LINE BREAK: 000A]chosen by the professor, are you?[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]You should go home first and have somebody[LINE BREAK: 000A]help you prepare for your journey!
- Russian draft: О! Ты один из детей,[LINE BREAK: 000A]которых выбрал профессор?[PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Сначала зайди домой и попроси помочь[LINE BREAK: 000A]собраться в путешествие!

### `a/0/8/2` · member `0049/0` · message `58`

- Source SHA-256: `019476c4d5fcccee98ff335709c62deaf7650331f59193f3f8baf876be06da5c`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Hey there! Looks like you found[LINE BREAK: 000A]somebody at home to help you pack![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Oh, and make sure you bring a bunch[LINE BREAK: 000A]of Poké Balls and Potions, all right?
- Russian draft: Привет! Вижу, дома тебе помогли[LINE BREAK: 000A]собраться![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Не забудь взять с собой побольше[LINE BREAK: 000A]Покеболов и зелий!

### `a/0/8/2` · member `0049/0` · message `59`

- Source SHA-256: `dfa2a2793ea26d89229ab6fd17562db07195f72fe2e9b71c4a1eb622fe385be7`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Hey, Pokémon Trainer![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]If you set foot in the tall grass,[LINE BREAK: 000A]a wild Pokémon will pop out![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]But you’ll be fine, because your[LINE BREAK: 000A]Pokémon partner will battle for you!
- Russian draft: Эй, тренер покемонов![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Если войдёшь в высокую траву,[LINE BREAK: 000A]может появиться дикий покемон![PAGE BREAK: 0010 0001 BE01][LINE BREAK: 000A]Но не бойся: твой покемон-напарник[LINE BREAK: 000A]сразится за тебя!

### `a/0/8/2` · member `0049/0` · message `70`

- Source SHA-256: `23eabaea6806945c1e09b17d5714ca1590efe1c7ea3e412c24aab491e9dfd133`
- Source versions: base
- Context: Aquacorde opening scene (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Aquacorde Town[LINE BREAK: 000A]Water and civilization in harmony.
- Russian draft: Аквакорд-таун[LINE BREAK: 000A]Вода и цивилизация в согласии.

## Starter selection interface

### `a/0/7/4` · member `0063/0` · message `0`

- Source SHA-256: `d18ab01158d01b563344d2a899ba25228436f8cfd3e38ade81029da37d1312c5`
- Source versions: base, update-1.5
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Choose a Pokémon.
- Russian draft: Выбери покемона.

### `a/0/7/4` · member `0063/0` · message `1`

- Source SHA-256: `32d4644d4ae7a1ccd310d335d6290d07738d6ce1aa40a251df915eda3663bfca`
- Source versions: base, update-1.5
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The Grass-type Pokémon[LINE BREAK: 000A][VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000]
- Russian draft: Травяной покемон[LINE BREAK: 000A][VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000]

### `a/0/7/4` · member `0063/0` · message `2`

- Source SHA-256: `6e3e7d3dacb9bb072ab6a6c019ec7e48d83a907afa66a7bb590c50abe2ec3329`
- Source versions: base, update-1.5
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The Fire-type Pokémon[LINE BREAK: 000A][VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000]
- Russian draft: Огненный покемон[LINE BREAK: 000A][VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000]

### `a/0/7/4` · member `0063/0` · message `3`

- Source SHA-256: `31a72df3bea145b55c0f1499e3d21a49a4cbacfbd0134e296fb638aed5d8eba8`
- Source versions: base, update-1.5
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The Water-type Pokémon[LINE BREAK: 000A][VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000]
- Russian draft: Водный покемон[LINE BREAK: 000A][VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000]

### `a/0/7/4` · member `0063/0` · message `4`

- Source SHA-256: `1feda56eb61f2cd058c287b39e411111e2e97346ddbcba95127139f248c73b47`
- Source versions: base, update-1.5
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: Choose this Pokémon?
- Russian draft: Выбрать этого покемона?

### `a/0/7/4` · member `0063/0` · message `5`

- Source SHA-256: `83e55beebffb869b239872ea572f3c629c56fa8075ab282046718917d79e0c61`
- Source versions: base, update-1.5
- Context: protagonist branch, starter UI, or early-game location (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: You chose [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000]!
- Russian draft: Ты выбрал [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000]!

## First-battle messages

The records are battle templates keyed by message ID. Which templates occur during each starter matchup is conditional and must be checked in-game.

### `a/0/7/4` · member `0124/0` · message `71`

- Source SHA-256: `f826dcae4593ce62243733f7332a2f59ecc1c9842daf5809cb3cd5ee835d36ee`
- Source versions: base, update-1.5
- Context: general first-battle UI templates (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: What will [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 010C 0000] do?
- Russian draft: Что будет делать [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 010C 0000]?

### `a/0/7/4` · member `0124/0` · message `72`

- Source SHA-256: `bd69bed2611224ae437ada247cf16b9f70f4e348b0ca0a23cab88450e0eb5249`
- Source versions: base, update-1.5
- Context: general first-battle UI templates (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: What will [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000] do?
- Russian draft: Что будет делать [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0100 0000]?

### `a/0/7/4` · member `0125/0` · message `0`

- Source SHA-256: `2409f4073bf7c7d80a767ef9a84b172c9ee3d26439aa1af942f8178ea95b52ec`
- Source versions: base, update-1.5
- Context: general first-battle UI templates (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0102 0000] fainted!
- Russian draft: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0102 0000] выбыл из боя!

### `a/0/7/4` · member `0125/0` · message `1`

- Source SHA-256: `9f3ee5194dcfe92f7e17e4893a36dee804e7e527ab7f881fd0bdf51d3851c81e`
- Source versions: base, update-1.5
- Context: general first-battle UI templates (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The wild [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0102 0000] fainted!
- Russian draft: Дикий [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0102 0000] выбыл из боя!

### `a/0/7/4` · member `0125/0` · message `2`

- Source SHA-256: `d39107027b4c52f80518ee757a8dd65cd9d9cd5d07da210bb9ed4094cdcd161f`
- Source versions: base, update-1.5
- Context: general first-battle UI templates (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The opposing [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0102 0000] fainted!
- Russian draft: Вражеский [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0102 0000] выбыл из боя!

### `a/0/7/4` · member `0126/0` · message `3`

- Source SHA-256: `dc937d05c16dbe92656845559482071f0cbcd6dc4d28e377ebf73753541b9c3a`
- Source versions: base, update-1.5
- Context: starter first-battle move message (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Pound!
- Russian draft: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] бьёт «Тяжёлым ударом»!

### `a/0/7/4` · member `0126/0` · message `4`

- Source SHA-256: `6333dc6560cff2faca7ab7b369e785bdd3d69488e113275ebabeb55f1f5bf57d`
- Source versions: base, update-1.5
- Context: starter first-battle move message (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The wild [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Pound!
- Russian draft: Дикий [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] бьёт «Тяжёлым ударом»!

### `a/0/7/4` · member `0126/0` · message `5`

- Source SHA-256: `bc15d4fb644150ccd3b40f3d979085d6fd97e04ff01a62c37deca6fb6b70411d`
- Source versions: base, update-1.5
- Context: starter first-battle move message (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The opposing [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Pound!
- Russian draft: Вражеский [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] бьёт «Тяжёлым ударом»!

### `a/0/7/4` · member `0126/0` · message `30`

- Source SHA-256: `410efcfc9f3e7e30bb6b059a491a98bcfc6b97d27ad486353c8824c2b93361d6`
- Source versions: base, update-1.5
- Context: general first-battle UI templates (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Scratch!
- Russian draft: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] применяет атаку «Царапание»!

### `a/0/7/4` · member `0126/0` · message `31`

- Source SHA-256: `880347a1f08e758c51c5b500b4ad04483ed9722b8675b9c0c41e6fa6b6f68c6d`
- Source versions: base, update-1.5
- Context: general first-battle UI templates (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The wild [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Scratch!
- Russian draft: Дикий [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] применяет атаку «Царапание»!

### `a/0/7/4` · member `0126/0` · message `32`

- Source SHA-256: `ec6ce0a6f24b013b215f302d032c46c2bfb9c40fed22675f836ee4e9fed8b605`
- Source versions: base, update-1.5
- Context: general first-battle UI templates (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The opposing [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Scratch!
- Russian draft: Покемон противника [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] применяет атаку «Царапание»!

### `a/0/7/4` · member `0126/0` · message `66`

- Source SHA-256: `bfd48728c4febe267f67f5cdc7a933d78df97425382909eff0f10ffb6d052374`
- Source versions: base, update-1.5
- Context: starter first-battle move message (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Vine Whip!
- Russian draft: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] применяет «Плеть-лиану»!

### `a/0/7/4` · member `0126/0` · message `67`

- Source SHA-256: `cc382dc8ed706e853182b290c67de2a45b247ee518b4fdfe638c96b0874a2ca8`
- Source versions: base, update-1.5
- Context: starter first-battle move message (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The wild [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Vine Whip!
- Russian draft: Дикий [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] применяет «Плеть-лиану»!

### `a/0/7/4` · member `0126/0` · message `68`

- Source SHA-256: `37f8cd133016051de5c56072fb05443557efd95cf9920192b7adee0a41f1e175`
- Source versions: base, update-1.5
- Context: starter first-battle move message (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The opposing [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Vine Whip!
- Russian draft: Вражеский [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] применяет «Плеть-лиану»!

### `a/0/7/4` · member `0126/0` · message `99`

- Source SHA-256: `47d5c46da2b3b4e3f2b832ca85859f7e88e1e40e01c11757bc776fdc66f0bbae`
- Source versions: base, update-1.5
- Context: general first-battle UI templates (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Tackle!
- Russian draft: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] применяет атаку «Бросок»!

### `a/0/7/4` · member `0126/0` · message `100`

- Source SHA-256: `4606067f6c07068c551a7f810392ef4e0f030ecf101c60fcb1475ca046d8c297`
- Source versions: base, update-1.5
- Context: general first-battle UI templates (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The wild [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Tackle!
- Russian draft: Дикий [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] применяет атаку «Бросок»!

### `a/0/7/4` · member `0126/0` · message `101`

- Source SHA-256: `e747ad995fffb2e1fa6eb2ddf52ae2283d7ed61d9c7415b388861b0f5a690b8a`
- Source versions: base, update-1.5
- Context: general first-battle UI templates (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The opposing [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Tackle!
- Russian draft: Покемон противника [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] применяет атаку «Бросок»!

### `a/0/7/4` · member `0126/0` · message `117`

- Source SHA-256: `6788c4282a80bb087c87223d8f3b021136ab6662e422fe6c81284fff94479410`
- Source versions: base, update-1.5
- Context: starter first-battle move message (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Tail Whip!
- Russian draft: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] применяет «Виляние хвостом»!

### `a/0/7/4` · member `0126/0` · message `118`

- Source SHA-256: `51ed45242aba221fc653d50033217cbadec9861cfc5dd61e5780851203c25aa6`
- Source versions: base, update-1.5
- Context: starter first-battle move message (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The wild [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Tail Whip!
- Russian draft: Дикий [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] применяет «Виляние хвостом»!

### `a/0/7/4` · member `0126/0` · message `119`

- Source SHA-256: `573ec089ffbc1dfbc01fdb3d7acf34cab0bb15c2175937db7e47096eb478e6cc`
- Source versions: base, update-1.5
- Context: starter first-battle move message (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The opposing [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Tail Whip!
- Russian draft: Вражеский [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] применяет «Виляние хвостом»!

### `a/0/7/4` · member `0126/0` · message `135`

- Source SHA-256: `3772b6362f984b455730d315373fc8c18d659ecf45a1907d46480f90f3d7dbef`
- Source versions: base, update-1.5
- Context: general first-battle UI templates (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Growl!
- Russian draft: [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] применяет атаку «Рычание»!

### `a/0/7/4` · member `0126/0` · message `136`

- Source SHA-256: `886a4300315fb9f187c01566400ed9ac4157fd90a830f7c47bc09023fda05728`
- Source versions: base, update-1.5
- Context: general first-battle UI templates (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The wild [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Growl!
- Russian draft: Дикий [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] применяет атаку «Рычание»!

### `a/0/7/4` · member `0126/0` · message `137`

- Source SHA-256: `643bf3b168d75197b7346a71397fa6865ca946c686c1c786341db28439bca9ac`
- Source versions: base, update-1.5
- Context: general first-battle UI templates (trigger not runtime-verified unless stated above)
- State: `draft`; human approval: pending
- English: The opposing [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] used Growl!
- Russian draft: Покемон противника [VARIABLE / PLACEHOLDER CONTROL: 0010 0002 0101 0000] применяет атаку «Рычание»!

## Runtime result recording

Record each game and protagonist choice separately. Mark only observed rendering results; do not promote draft/review status based on structural tests.

| Game | Protagonist | Scene/message IDs | Text visible | Layout/control result |
|---|---|---|---|---|
| Pokémon X | Male |  |  |  |
| Pokémon X | Female |  |  |  |
| Pokémon Y | Male |  |  |  |
| Pokémon Y | Female |  |  |  |
