// theme.js
import { orange, red, blue } from '@material-ui/core/colors';


export const theme = {
  primaryLight: '#0D0C1D',
  primaryDark: '#EFFFFA',
  primaryHover: '#343078',
  overrides: {
    MuiOutlinedInput: {
        root:{
            color: 'black',
            background: red[100],

        }
    },
},
palette: {
    primary: {
        light: blue[300],
        main: blue[500],
        dark: blue[700]
    },
    secondary: {
        light: orange[300],
        main: orange[500],
        dark: orange[700]
    },
    type: 'light',
    text: {
        label: "rgba(0, 0, 0, 0.87)",
        disabled: "rgba(255, 255, 255, 0.5)",
        hint: "rgba(255, 255, 255, 0.5)",
        icon: "rgba(255, 255, 255, 0.5)",
        primary: "#000",
        secondary: "rgba(255, 255, 255, 0.7)" ,
    },
},
typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    fontSize: 14,
    fontWeightLight: 300,
    fontWeightRegular: 400,
    fontWeightMedium: 500,
    fontWeightBold: 700
},
}