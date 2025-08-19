var gulp = require('gulp');
var copy = require('gulp-copy');

// Copy bulk assets that already have css/js folder structure under dist
gulp.task('copy-bulk', function () {
  return gulp
    .src([
      './node_modules/bootstrap/dist/**/*.+(css|js|map)',
      './node_modules/select2/dist/**/*.+(css|js|map)'
    ], { allowEmpty: true })
    .pipe(copy('./assets/', { prefix: 3 }));
});

// Ensure jQuery lands in assets/js (jquery package doesn't have css/js subfolders)
gulp.task('copy-jquery', function () {
  return gulp
    .src([
      './node_modules/jquery/dist/jquery.min.js',
      './node_modules/jquery/dist/jquery.min.map'
    ], { allowEmpty: true })
    .pipe(gulp.dest('./assets/js'));
});

// Ensure select2 bootstrap theme css lands in assets/css (file sits directly under dist)
gulp.task('copy-select2-theme', function () {
  return gulp
    .src([
      './node_modules/select2-bootstrap-5-theme/dist/select2-bootstrap-5-theme.min.css',
      './node_modules/select2-bootstrap-5-theme/dist/select2-bootstrap-5-theme.min.css.map'
    ], { allowEmpty: true })
    .pipe(gulp.dest('./assets/css'));
});

// Copy favicon(s)
gulp.task('copy-favicon', function () {
  return gulp
    .src(['./favicon.svg'], { allowEmpty: true })
    .pipe(gulp.dest('./assets'));
});

gulp.task('copy-assets', gulp.series('copy-bulk', 'copy-jquery', 'copy-select2-theme', 'copy-favicon'));

gulp.task('default', gulp.series('copy-assets')); 