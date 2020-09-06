import styled from 'styled-components'
import { Grid } from '../pdvmComponents/PdvmRaster';


export const PdvmFlexBox = styled(Grid)`
${({ theme }) => `
  color: ${theme.palette.text.secondary.light}} ;
  background-color: ${theme.palette.text.secondary.dark} ;
  box-shadow: 3px 3px 1px ${theme.palette.primary.dark};
  margin-bottom: 0.5em;
​​  `}
`;
