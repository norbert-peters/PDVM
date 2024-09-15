import { createMuiTheme } from '@material-ui/core/styles';
import { orange, grey } from '@material-ui/core/colors';


export const PdvmDarkTheme = createMuiTheme({ 
    overrides: {
        MuiOutlinedInput: {
            root:{
                color: 'black',
                background: grey[100],

            }
        },
    },
    palette: {
        primary: {
            light: grey[100],
            main: grey[500],
            dark: grey[900],
        },
        secondary: {
            light: orange[100],
            main: orange[500],
            dark: orange[900],
        },
        type: 'dark',
        text: {
            label: "rgba(0, 0, 0, 0.87)",
            disabled: "rgba(0, 0, 0, 0.38)",
            hint: "rgba(0, 0, 0, 0.38)",
            icon: "rgba(0, 0, 0, 0.38)",
            primary: "rgba(245, 245, 245, 0.87)",
            secondary: "rgba(0, 0, 0, 0.54)",
        }
    },
    typography: {
        fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
        fontSize: 14,
        fontWeightLight: 300,
        fontWeightRegular: 400,
        fontWeightMedium: 500,
        fontWeightBold: 700,
    },
})
