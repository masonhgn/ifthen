module.exports = {
    env: {
        browser: true,
        es2021: true,
        node: true,
        jest: true
    },
    extends: [
        'eslint:recommended'
    ],
    parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module'
    },
    rules: {
        'no-console': 'off', // Allow console.log in game code
        'no-unused-vars': 'warn',
        'no-undef': 'error',
        'semi': ['error', 'always'],
        'quotes': ['error', 'single'],
        'indent': ['error', 4],
        'comma-dangle': ['error', 'never'],
        'object-curly-spacing': ['error', 'always'],
        'array-bracket-spacing': ['error', 'never'],
        'space-before-function-paren': ['error', 'never'],
        'keyword-spacing': ['error', { 'before': true, 'after': true }],
        'space-infix-ops': 'error',
        'eol-last': ['error', 'always'],
        'no-trailing-spaces': 'error',
        'no-multiple-empty-lines': ['error', { 'max': 2, 'maxEOF': 1 }]
    },
    globals: {
        'io': 'readonly',
        'gameId': 'readonly',
        'closeNotification': 'readonly',
        'showSolvePage': 'readonly'
    }
};
