var gulp = require('gulp');
var copy = require('gulp-copy');

gulp.task('copy-assets', function () {
  return gulp
    .src([
      './node_modules/bootstrap/dist/**/*.+(css|js|map)',
      './node_modules/jquery/dist/**/*.+(js|map)',
      './node_modules/select2/dist/**/*.+(css|js|map)',
      './node_modules/select2-bootstrap-5-theme/dist/**/*.+(css|js|map)'
    ], { allowEmpty: true })
    .pipe(copy('./assets/', { prefix: 3 }));
});

gulp.task('default', gulp.series('copy-assets')); 