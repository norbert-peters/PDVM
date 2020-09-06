import { Box } from '@material-ui/core'
import styled from "styled-components";
 
export const PdvmBox = styled(Box)`
  ${({ theme }) => `
    display: flex;
    flex-direction: row;
    color: ${theme.palette.text.primary.dark}} ;
    background-color: ${theme.palette.secondary.light};
    position: relative;
    margin-left: 15px;
​​  `}
`;
  