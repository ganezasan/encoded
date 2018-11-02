// Require all components to ensure javascript load ordering
require('./lib');
require('./antibody');
require('./app');
require('./award');
require('./image');
require('./biosample');
require('./collection');
require('./dataset');
require('./dbxref');
require('./errors');
require('./experiment');
require('./genetic_modification');
require('./footer');
require('./globals');
require('./graph');
require('./doc');
require('./donor');
require('./file');
require('./item');
require('./page');
require('./platform');
require('./search');
require('./report');
require('./matrix');
require('./target');
require('./publication');
require('./pipeline');
require('./software');
require('./news');
require('./testing');
require('./edit');
require('./inputs');
require('./blocks');
require('./user');
require('./schema');
require('./summary');
require('./region_search');
require('./regulome_summary');
require('./auditmatrix');
require('./gene');


module.exports = require('./app');
