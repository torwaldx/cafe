INSERT IGNORE INTO `categories` (`id`, `name`) VALUES
	(2, 'ресторан'),
	(3, 'бар'),
	(4, 'кафе'),
	(5, 'кондитерская'),
	(6, 'доставка еды и обедов'),
	(7, 'рыба и морепродукты'),
	(8, 'быстрое питание'),
	(9, 'кофейня'),
	(10, 'аренда площадок для культурно-массовых мероприятий'),
	(11, 'пекарня'),
	(12, 'банкетный зал');

INSERT IGNORE INTO `sources` (`id`, `source_type`, `is_active`, `is_deleted`, `processed_at`) VALUES
	(1, 'telegram', 1, 0, NULL),
	(2, 'telegram', 1, 0, NULL),
	(3, 'telegram', 1, 0, NULL),
	(4, 'telegram', 1, 0, NULL),
	(5, 'telegram', 1, 0, NULL),
	(6, 'instagram', 1, 0, NULL),
	(7, 'instagram', 1, 0, NULL),
	(8, 'instagram', 1, 0, NULL),
	(9, 'instagram', 1, 0, NULL),
	(10, 'instagram', 1, 0, NULL),
	(11, 'instagram', 1, 0, NULL),
	(12, 'instagram', 1, 0, NULL),
	(13, 'instagram', 1, 0, NULL),
	(14, 'instagram', 1, 0, NULL),
	(15, 'instagram', 1, 0, NULL);

INSERT IGNORE INTO `instagram_accounts` (`id`, `inst_user_id`, `inst_username`, `last_message_time`, `source`) VALUES
	(1, 57851082611, 'tvoya.moscow', 0, 6),
	(2, 49049849652, 'vilka.mgzn', 0, 7),
	(3, 2190469818, 'breakfastinmsk', 0, 8),
	(4, 2239928699, 'coffeeinmoscow', 0, 9),
	(5, 38548710178, 'moscow_pike', 0, 10),
	(6, 47530686636, 'walk.eat.repeat_msk', 0, 11),
	(7, 44814843232, 'secret_guide', 0, 12),
	(8, 21855962518, 'msc.places', 0, 13),
	(9, 54761588422, 'poidem_moscoww', 0, 14),
	(10, 233903823, 'anna.gamil', 0, 15);

INSERT IGNORE INTO `tg_channels` (`id`, `source`, `tg_name`, `tg_link`, `last_message_id`, `tg_chat_id`) VALUES
	(1, 1, '@vkusonomika', NULL, 0, NULL),
	(2, 2, '@moskva_food', NULL, 0, NULL),
	(3, 3, '@mskrestfood', NULL, 0, NULL),
	(4, 4, '@newinmsk', NULL, 0, NULL),
	(5, 5, '@msk_res', NULL, 0, NULL);

INSERT IGNORE INTO `tasks` (`id`, `task`, `script_module`, `count`, `schedule_type`, `schedule_time`, `is_active`) VALUES
	(1, 'Получение новых сообщений из telegram', 'collector.tg_extractor', 6, 'hour', '\:05', 1),
	(2, 'Получение новых постов из instagram', 'collector.ig_extractor', 1, 'day', '06\:00', 1),
	(3, 'Поиск кафе в яндекс картах', 'collector.ymap_parser', 1, 'day', '07\:15', 1),
	(4, 'Очистка ненужных сообщений', 'collector.db_service', 10, 'day', '00:55', 1);
