import pymongo
import BidTrackerScraper
import time

bts = BidTrackerScraper.BidTrackerScraper()
bts._connect_to_mongodb()
new_auctions = ['204989814', '189476998', '100812617', '340086794', '164609657', '134156093', '169831728', '364795748', '831411737', '639906446', '438388454', '939121130', '263196348', '764494772', '982103802', '394464319', '197987186', '589726796', '489647801', '171167011', '241823323', '860887394', '613814116', '526081446', '775836189', '539010417', '883000481', '708958911', '448289740', '230631907', '280845139', '207328946', '126304171', '555669324', '580589949', '836804509', '652626176', '552877979', '215671060', '895738200', '723806157', '227284500', '242178377', '909296013', '910107213', '114493590', '741186839', '598508747', '331884612', '515833000', '180313616', '285607809', '280219948', '631131549', '679192013', '265437424', '973316339', '757476241', '869747830', '661972447', '284339853', '131705646', '529306079', '983322923', '337214234', '759818017', '447968977', '282998589', '217360733', '957670248', '585935641', '219982099', '514939003', '686549280', '686504939', '557637580', '626322958', '522582580', '394062794', '851459852', '317008238', '842261468', '735804354', '965422859', '256513316', '578464598', '708175216', '502032347', '666629217', '796676479', '481181957', '732133581', '528905025', '302345095', '348223373', '721463418', '715079996', '473786907', '502575853', '155245618', '692840929', '266698031', '541163892', '707267254', '968149787', '322414963', '851380566', '135006010', '620270377', '499871459', '692847100', '216439906', '961978019', '791968390', '921847314', '602205615', '498600827', '726234546', '924980014', '813847537', '262568084', '872121686', '518764368', '715276809', '676556224', '810466547', '116198006', '304462612', '647715333', '447037174', '805911316', '884967731', '908944514', '961910084', '377605162', '542808605', '825853096', '936152652', '941534793', '225683429', '684194372', '724881231', '310692484', '345701403', '565362524', '880100755', '677155045', '712567248', '857111030', '824983339', '817756454', '891996149', '789298700', '448629317', '278239590', '543455760', '840360168', '714602623', '631131758', '845202665', '503802180', '583431984', '195941914', '946418729', '173421012', '555031021', '350048821', '786167331', '524823210', '158010664', '809284725', '299273023', '364834126', '198161308', '247683065', '865659635', '781609424', '956804573', '947319741', '782252973', '354705226', '391319454', '783428550', '236082560', '966549038', '885224778', '941354068', '812069384', '769827219', '298074716', '934489307', '154177016', '598645103', '560560525', '718141568', '252476632', '987205525', '281748989', '904025355', '184059651', '341973546', '395883983', '511703332', '739637061', '651474142', '448363047', '220353064', '138646887', '425559246', '935908274', '849588837', '876840081', '553487019', '784549885', '633005161', '446752694', '516895104', '580575761', '210439279', '405792554', '620619051', '807896118', '147617106', '828586298', '866202760', '845712817', '113243349', '518646873', '610954161', '994454417', '342999313', '790710421', '637925898', '602593953', '853009788', '773067171', '267095414', '664965871', '114791901', '792042151', '607793611', '335798631', '790922978', '427144037', '641761936', '717313042', '526198463', '477128461', '766182542', '252498379', '500781565', '987661616', '490975197', '809248250', '815641783', '246956297', '288732740', '624147570', '980223191', '431175559', '919174017', '975025825', '136620709', '338895225', '175572754', '171790369', '160025469', '621959890', '187387193', '205007617', '795364299', '364703210', '820229198', '947465463', '427441634', '803425845', '985015216', '917222089', '809534041', '695205299', '759087607', '895235093', '525117630', '584036542', '931696338', '563218752', '268660977', '518090778', '425000773', '175572420', '733740301', '531663650', '261369264', '552918684', '929166648', '934629521', '359171185', '548599241', '939892186', '761276465', '850402460', '832623756', '532028517', '326515343', '775922373', '343438295', '252695847', '169987036', '616799024', '280299057', '863544513', '416071913', '616197640', '858453635', '942965333', '609826058', '381980632', '781246394', '403422492', '303006564', '319278976', '437898252', '874281047', '505164789', '963579819', '358733104', '331136146', '861484976', '568164925', '395164078', '834849427', '667863412', '358784243', '748100628', '122215682', '832367275', '863661801', '203685714', '121693536', '495376221', '930035513', '286799052', '212425841', '675712646', '116289274', '937939818', '962763634', '736183569', '849751707', '207827959', '381012536', '776887047', '890784826', '658529414', '117431863', '844419579', '366968543', '129734056', '620646004', '999568617', '915902155', '402776241', '915884861', '808308730', '455744736', '532689355', '108631092', '597755471', '661403756', '168920146', '973745036', '372513836', '735136610', '815017491', '989007877', '338867810', '671353728', '477067270', '895208647', '614239371', '560162268', '768782245', '564427484', '245402743', '522384064', '812889183', '302384676', '388119112', '108158202', '176109337', '294346964', '790146526', '184798276', '504351463', '601713251', '944995211', '118588752', '418955336', '940227977', '832770276', '622664459', '605030839', '827162096', '432388114', '840196443', '915130413', '615638241', '231718394', '753803182', '937633405', '697257817', '577365397', '622941140', '684267646', '156800787', '379466884', '111225475', '830602675', '534057779', '731116656', '623782246', '582021581', '209767812', '694380684', '634613453', '595744191', '230730573', '988122121', '642096824', '377060862', '217437494', '881575000', '920073100', '988705077', '991652242', '503362193', '220583910', '202828195', '123253803', '943135107', '515588232', '858424544', '595852112', '291646997', '314074785', '967556465', '269661349', '570847380', '399613921', '539006293', '804476416', '458629794', '570784326', '368686731', '177178575', '894478013', '129760629', '924512055', '160289720', '720832908', '655157693', '354499810', '690516038', '793462229', '947503721', '915195630', '453012864', '543434015', '125330594', '310912769', '674762562', '471009713', '743586764', '764516459', '790465192', '399413360', '913428673', '829913771', '807943727', '281017647', '136344128', '911252369', '289101115', '956459683', '773644877', '139545722', '245462802', '688185297', '792679797', '263993263', '881328575', '722019684', '380770285', '507809821', '740594423', '321559855', '809861047', '456475282', '346909928', '598788459', '126523584', '131156901', '302835787', '495972690', '655160585', '338030792', '723163566', '452408430', '338392658', '127409845', '938933992', '210860391', '828865392', '469184266', '406687229', '681061907', '522012335', '954468143', '738522269', '815145694', '155252573', '901850680', '211785068', '961596555']

i = 0

bts.login(0)
for aid in new_auctions:
    print(i, len(new_auctions))
    if not (bts.pages_collection.find_one({"_id": aid})):
        auction = bts._scrape_auction(aid, "whatever", .5)
        bts.pages_collection.insert_one(auction)
    i += 1
